#!/usr/bin/env python
# coding: utf-8

# # Initial setup
# setup of the Dataset classes


import json
import os.path
from pathlib import Path
from typing import Dict, List, Tuple
import math

import cv2
import numpy as np
import itertools
# from pytorch example:https://docs.pytorch.org/tutorials/intermediate/transformer_building_blocks.html#the-above-building-blocks-are-all-you-need-as-of-october-2024
# modified to make query and value project identically:TODO
import torch
import torchvision
from datasets import load_dataset
from scipy.interpolate import CloughTocher2DInterpolator
from torch.profiler import record_function
from torch.utils.data import Dataset
from torchvision.io import decode_image
from torchvision.transforms import v2
from torchvision.ops import masks_to_boxes

from zoo.SuperPointPretrainedNetwork.demo_superpoint import SuperPointNet


def process_json_annotations(filename: str) -> List:
    """reads a via generated json annotation file to convert to individual masks."""
    masks = {}
    with open(filename, encoding="utf-8") as fileptr:
        dump = json.load(fileptr)
    file_struct = {"filename", "size", "regions", "file_attributes"}
    for k in dump.keys():
        assert set(dump[k].keys()) <= file_struct, "File format err"
    for k, image in dump.items():
        rects = list(
            filter(lambda x: x["shape_attributes"]["name"] == "rect", image["regions"])
        )
        n_trains = int(image["file_attributes"]["n_trains"])
        assert n_trains == len(
            rects
        ), f"length mismatch in {k}. expected{n_trains}, got {len(rects)}"
        masks[image["filename"]] = gen_mask(image["regions"], (720, 1280), n_trains)
    return masks


@torch.no_grad()
def gen_mask(
    regions: List[Dict], image_size: Tuple[int], n_trains: int, cutoff=0.2
):  # -> torch.Tensor
    bboxs = sorted(
        filter(lambda x: x["shape_attributes"]["name"] == "rect", regions),
        key=lambda x: x["region_attributes"]["bbox_id"],
    )
    sorted_points = [
        list(
            filter(
                lambda x: int(x["region_attributes"]["bbox_id"]) == i
                and x["shape_attributes"]["name"] == "point",
                regions,
            )
        )
        for i in range(n_trains)
    ]
    mask = np.zeros((n_trains, image_size[1], image_size[0]), dtype=np.bool)
    for i in range(n_trains):
        points = []
        values = []
        for point in sorted_points[i]:
            posx = point["shape_attributes"]["cx"]
            posy = point["shape_attributes"]["cy"]
            label = float(point["region_attributes"]["entity"] == "train")
            points.append((posx, posy))
            values.append(label)
        points = np.array(points)
        values = np.array(values)
        interp = CloughTocher2DInterpolator(points, values, fill_value=0.0)
        bbox = bboxs[i]["shape_attributes"]
        x0, y0, width, height = bbox["x"], bbox["y"], bbox["width"], bbox["height"]
        X = np.arange(x0, x0 + width, 1)
        Y = np.arange(y0, y0 + height, 1)
        X, Y = np.meshgrid(X, Y)
        Z = interp(X, Y) > cutoff
        mask[i, y0 : y0 + height, x0 : x0 + width] = Z
    return torch.from_numpy(mask.astype(float))


def get_center(mask) -> np.array:
    n_train = mask.shape[0]
    return [
        tuple(int(np.average(indices).item()) for indices in np.where(mask[i].T))
        for i in range(n_train)
    ]

def np_readout(semi, conf_thresh=0.15):
    # --- Process points.
    #print('semi',semi.shape)
    dense = np.exp(semi)  # Softmax.
    dense = dense / (np.sum(dense, axis=0) + 0.00001)  # Should sum to 1.
    # Remove dustbin.
    nodust = dense[:-1, :, :]
    # Reshape to get full resolution heatmap.
    Hc = int(H / CELL)
    Wc = int(W / CELL)
    #print('nodust shape pre trasnpose', nodust.shape)
    nodust = nodust.transpose(1, 2, 0)
    #print('nodust shape', nodust.shape)
    heatmap = np.reshape(nodust, [Hc, Wc, CELL, CELL])
    #print('heatmap pre shape', heatmap.shape)
    heatmap = np.transpose(heatmap, [0, 2, 1, 3])
    #print('heatmap pre 2 shape', heatmap.shape)
    heatmap = np.reshape(heatmap, [Hc * CELL, Wc * CELL])
    #print('heatmap shape', heatmap.shape)
    xs, ys = np.where(heatmap >= conf_thresh)  # Confidence threshold.
    return (xs,ys),heatmap
    
def quick_readout(pred_blocks, conf_thresh=0.15):
    shuffel = torch.nn.PixelShuffle(8)
    pred_blocks = torch.nn.Softmax()(pred_blocks)[:-1]
    dense = shuffel(pred_blocks).squeeze()
    return torch.nonzero(dense >= conf_thresh, as_tuple=True), dense

def gen_keypoints(img, net, conf_thresh=0.015, nms_dist=4):
    # pylint: disable=too-many-statements,too-many-locals
    """Process a numpy image to extract points and descriptors.
    Input
      img - HxW numpy float32 input image in range [0,1].
    Output
      corners - 3xN numpy array with corners [x_i, y_i, confidence_i]^T.
      desc - 256xN numpy array of corresponding unit normalized descriptors.
      heatmap - HxW numpy heatmap in range [0,1] of point confidences.
    """

    def nms_fast(in_corners, H, W, dist_thresh):
        """
        Run a faster approximate Non-Max-Suppression on numpy corners shaped:
          3xN [x_i,y_i,conf_i]^T

        Algo summary: Create a grid sized HxW. Assign each corner location a 1, rest
        are zeros. Iterate through all the 1's and convert them either to -1 or 0.
        Suppress points by setting nearby values to 0.

        Grid Value Legend:
        -1 : Kept.
         0 : Empty or suppressed.
         1 : To be processed (converted to either kept or supressed).

        NOTE: The NMS first rounds points to integers, so NMS distance might not
        be exactly dist_thresh. It also assumes points are within image boundaries.

        Inputs
          in_corners - 3xN numpy array with corners [x_i, y_i, confidence_i]^T.
          H - Image height.
          W - Image width.
          dist_thresh - Distance to suppress, measured as an infinty norm distance.
        Returns
          nmsed_corners - 3xN numpy matrix with surviving corners.
          nmsed_inds - N length numpy vector with surviving corner indices.
        """
        grid = np.zeros((H, W)).astype(int)  # Track NMS data.
        inds = np.zeros((H, W)).astype(int)  # Store indices of points.
        # Sort by confidence and round to nearest int.
        inds1 = np.argsort(-in_corners[2, :])
        corners = in_corners[:, inds1]
        rcorners = corners[:2, :].round().astype(int)  # Rounded corners.
        # Check for edge case of 0 or 1 corners.
        if rcorners.shape[1] == 0:
            return np.zeros((3, 0)).astype(int), np.zeros(0).astype(int)
        if rcorners.shape[1] == 1:
            out = np.vstack((rcorners, in_corners[2])).reshape(3, 1)
            return out, np.zeros((1)).astype(int)
        # Initialize the grid.
        for i, rc in enumerate(rcorners.T):
            grid[rcorners[1, i], rcorners[0, i]] = 1
            inds[rcorners[1, i], rcorners[0, i]] = i
        # Pad the border of the grid, so that we can NMS points near the border.
        pad = dist_thresh
        grid = np.pad(grid, ((pad, pad), (pad, pad)), mode="constant")
        # Iterate through points, highest to lowest conf, suppress neighborhood.
        count = 0
        for i, rc in enumerate(rcorners.T):
            # Account for top and left padding.
            pt = (rc[0] + pad, rc[1] + pad)
            if grid[pt[1], pt[0]] == 1:  # If not yet suppressed.
                grid[pt[1] - pad : pt[1] + pad + 1, pt[0] - pad : pt[0] + pad + 1] = 0
                grid[pt[1], pt[0]] = -1
                count += 1
        # Get all surviving -1's and return sorted array of remaining corners.
        keepy, keepx = np.where(grid == -1)
        keepy, keepx = keepy - pad, keepx - pad
        inds_keep = inds[keepy, keepx]
        out = corners[:, inds_keep]
        values = out[-1, :]
        inds2 = np.argsort(-values)
        out = out[:, inds2]
        out_inds = inds1[inds_keep[inds2]]
        return out, out_inds

    CELL = 8
    BORDER_REMOVE = 4
    assert img.ndim == 2, "Image must be grayscale."
    assert img.dtype == np.float32, "Image must be float32."
    H, W = img.shape[0], img.shape[1]
    inp = img.copy()
    inp = inp.reshape(1, H, W)
    inp = torch.from_numpy(inp)
    inp = torch.autograd.Variable(inp).view(1, 1, H, W)
    semi, coarse_desc = net.forward(inp)
    (xs,ys), heatmap = np_readout(semi.data.cpu().numpy().squeeze())
    if len(xs) == 0:
        return np.zeros((3, 0)), None, None
    pts = np.zeros((3, len(xs)))  # Populate point data sized 3xN.
    pts[0, :] = ys
    pts[1, :] = xs
    pts[2, :] = heatmap[xs, ys]
    pts, _ = nms_fast(pts, H, W, dist_thresh=nms_dist)  # Apply NMS.
    inds = np.argsort(pts[2, :])
    pts = pts[:, inds[::-1]]  # Sort by confidence.
    # Remove points along border.
    bord = BORDER_REMOVE
    toremoveW = np.logical_or(pts[0, :] < bord, pts[0, :] >= (W - bord))
    toremoveH = np.logical_or(pts[1, :] < bord, pts[1, :] >= (H - bord))
    toremove = np.logical_or(toremoveW, toremoveH)
    pts = pts[:, ~toremove]
    # --- Process descriptor.
    D = coarse_desc.shape[1]
    if pts.shape[1] == 0:
        desc = np.zeros((D, 0))
    else:
        # Interpolate into descriptor map using 2D point locations.
        samp_pts = torch.from_numpy(pts[:2, :].copy())
        samp_pts[0, :] = (samp_pts[0, :] / (float(W) / 2.0)) - 1.0
        samp_pts[1, :] = (samp_pts[1, :] / (float(H) / 2.0)) - 1.0
        samp_pts = samp_pts.transpose(0, 1).contiguous()
        samp_pts = samp_pts.view(1, 1, -1, 2)
        samp_pts = samp_pts.float()
        desc = torch.nn.functional.grid_sample(coarse_desc, samp_pts)
        desc = desc.data.cpu().numpy().reshape(D, -1)
        desc /= np.linalg.norm(desc, axis=0)[np.newaxis, :]
    return pts, desc, heatmap

def read_image(impath, img_size=(120, 160)):
    """Read image as grayscale and resize to img_size.
    Inputs
      impath: Path to input image.
      img_size: (W, H) tuple specifying resize size.
    Returns
      grayim: float32 numpy array sized H x W with values in range [0, 1].
    """
    grayim = cv2.imread(impath, 0)
    if grayim is None:
        raise FileNotFoundError(f"Error reading image {impath}")
    # Image is resized via opencv.
    interp = cv2.INTER_AREA
    grayim = cv2.resize(grayim, (img_size[1], img_size[0]), interpolation=interp)
    grayim = grayim.astype("float32") / 255.0
    return grayim


class MMRPifPafTune(Dataset):

    @torch.no_grad()
    def _interp_masks(self, interpolation_threshold):
        for i in range(len(self.prelabled_images) - 1):
            cur_img = self.prelabled_images[i]
            next_img = self.prelabled_images[i + 1]
            if cur_img.split("_")[0] != next_img.split("_")[0]:
                # not same sequence instance
                continue
            with record_function("check_file_exists"):
                cur_img_id = int(cur_img.split("_")[1].split(".")[0])
                next_img_id = int(next_img.split("_")[1].split(".")[0])
                dataset = cur_img.split("_")[0]
                inter_frames = [
                    f"{dataset}_{idx}.png" for idx in range(cur_img_id + 1, next_img_id)
                ]
                inter_frames = list(
                    filter(lambda x: os.path.isfile(self.root / x), inter_frames)
                )
            if len(inter_frames) > interpolation_threshold:
                # image gap too large
                continue
            source_img = self.pre_annotations[cur_img]
            if self.pre_annotations[next_img].shape[0] != source_img.shape[0]:
                # Todo interpt across varying masks number
                continue
            spacing = len(inter_frames) + 1
            img_diff = (self.pre_annotations[next_img] - source_img) / spacing
            with record_function("iter_steps"):
                for step in range(1, spacing):
                    self.masks[inter_frames[step - 1]] = source_img + img_diff * step

    @torch.no_grad()
    def _calc_centroid(self):
        new_masks = {}
        y_index = torch.arange(self.internal_size[0]).double()
        x_index = torch.arange(self.internal_size[1]).double()
        vector_field = (
            torch.cartesian_prod(y_index, x_index).reshape(2, 640, 480).double()
        )
        centroids = []
        self.fields = {}
        for k, mask in self.masks.items():
            with record_function("resize_mask"):
                mask = mask[None, :, :]
                mask = torch.squeeze(
                    torch.nn.functional.interpolate(mask, size=self.internal_size), 0
                )

            area = mask.sum(dim=(1, 2))
            with record_function("get_centroid"):
                # maybe i should store them
                y_center = torch.matmul(mask.sum(dim=2), y_index) / area
                x_center = torch.matmul(mask.sum(dim=1), x_index) / area
                kpts = torch.stack((y_center, x_center))
                kpts = torch.unsqueeze(kpts.T, 0)
            del y_center
            del x_center
            m_mask = mask.max(dim=0).values
            img_cords = torch.nonzero(m_mask)[None, :, :]
            with record_function("calc_NN"):
                dist = torch.cdist(img_cords.double(), kpts)
                pixel_entity_assigment = dist.squeeze().min(dim=1).indices
            # for each pixel in image calc vector to centroid
            # vector are coordinates
            # non relevant pixels have a vector to self/length 0

            idx = img_cords[0].T
            with record_function("assign_field"):
                tmp_field = vector_field.detach().clone()
                #print(kpts[0, pixel_entity_assigment])
                #print('kpts[0, pixel_entity_assigment] shape', kpts[0, pixel_entity_assigment].shape)
                tmp_field[:,idx[0], idx[1]] = kpts[0, pixel_entity_assigment].T
                self.fields[k] = tmp_field.float()
                del tmp_field
            new_masks[k] = mask.float()
        self.masks = new_masks

    @torch.no_grad()
    def _process_points(self):
        # access image->generate keypoints-> associate keypoints to mask
        if os.path.isfile("keypointlist.ph"):
            keypoints_list = torch.load("keypointlist.ph", weights_only=False)
            keypoint_embeds = torch.load("keypoint_embeds.ph", weights_only=False)
            assert len(keypoints_list) == len(self)
            assert len(keypoint_embeds) == len(self)
        else:
            keypoints_list = []
            keypoint_embeds = []
            for idx in range(len(self)):
                img_nameid = self.image_instances[idx]
                img_path = self.root / img_nameid
                image = read_image(img_path, img_size=self.internal_size)
                # show_np(image)
                pts, desc, heatmap = gen_keypoints(
                    image, self.model, conf_thresh=0.025, nms_dist=4
                )
                pts = torch.from_numpy(pts[0:2]).int()
                pts = torch.reshape(pts.T, (1, -1, 2))
                keypoints_list.append(pts)
                keypoint_embeds.append(torch.from_numpy(desc))
            torch.save(keypoints_list, "keypointlist.ph")
            torch.save(keypoint_embeds, "keypoint_embeds.ph")
        self.keypoints = keypoints_list
        self.keypoint_embeds = keypoint_embeds

    def __init__(self, root: Path, image_transforms=None, target_transforms=None, transforms=None, interpolation_threshold=150, debug=False):
        self.debug = debug
        if isinstance(root, str):
            self.root = Path(root)
        elif isinstance(root, Path):
            self.root = root
        self.transforms = transforms
        self.image_transforms = image_transforms
        self.target_transforms = target_transforms
        with record_function("process_annotations"):
            self.pre_annotations = process_json_annotations(
                "data/coco_fix_json(1).json"
            )
        self.prelabled_images = sorted(self.pre_annotations.keys())
        self.masks = (
            self.pre_annotations
        )
        self.internal_size = (640, 480)
        with record_function("interp_masks"):
            self._interp_masks(interpolation_threshold=interpolation_threshold)
        with record_function("calc_centroid"):
            self._calc_centroid()
        self.image_instances = sorted(self.masks.keys())
        self.n_examples = len(self.image_instances)
        # print(self.masks['woodbridge_191.png'][0].max())
        weights_path = "./zoo/SuperPointPretrainedNetwork/superpoint_v1.pth"
        with record_function("load_model"):
            self.model = SuperPointNet()
            self.model.load_state_dict(
                torch.load(weights_path, map_location=lambda storage, loc: storage)
            )
            self.model.eval()
        with record_function("process_points"):
            # listing of pregenerated keypoint locations for each image and their lable according to the mask
            self._process_points()

    def __len__(self):
        return self.n_examples

    def __getitem__(self, idx):
        img_nameid = self.image_instances[idx]
        img_path = self.root / img_nameid
        image = decode_image(img_path, mode='RGB')
        with torch.no_grad():
            image = v2.functional.resize(
                image, self.internal_size
            )
        target = {}
        mask = self.masks[img_nameid]  # .max(axis=0).values

        if self.debug:
            pts = self.keypoints[idx].squeeze()
            lpts = torch.reshape(pts.T, (2, -1))
            labels = mask[:, lpts[1], lpts[0]]
            target["poi"] = pts#.unsqueeze(0)   # nts_of_interest
            target["labels"] = labels#.unsqueeze(0) #== the mask
            target["image_id"] = img_nameid
            target['mask'] = mask
            target['bbox'] = masks_to_boxes(mask)
        else:
            target['mask'] = torch.amax(mask,0, keepdim=True)#.unsqueeze(0) 
        #target['mask'] = mask
        target["fields"] = self.fields[img_nameid]#.unsqueeze(0) 
        #target["masks"] = tv_tensors.Mask(self.masks[img_nameid])
        if self.image_transforms:
            image = self.image_transforms(image)
        if self.target_transforms:
            target = self.target_transforms(target)
        if self.transforms:
            image = self.transforms(image)
            target['mask'] = self.transforms(target['mask'])
            target['fields'] = self.transforms(target['fields'])
            target['bbox'] = self.transforms(target.get('bbox'))
        return image, target

class MMRFineTune(Dataset):
    @staticmethod
    def istrain(path: Path) -> bool:
        return path.parts[-2].contains("train")

    def __init__(self, root: Path, transform=None):
        if isinstance(root, str):
            self.root = Path(root)
        elif isinstance(root, Path):
            self.root = root
        self.transform = transform
        self.other_list = list(self.root.glob("other/*.jpg"))
        self.train_list = list(self.root.glob("train/*.jpg"))
        ds = load_dataset("zh-plus/tiny-imagenet")
        self.contrast = ds["train"]
        self.max_contrast = 0  # max num of contrast samples
        self.n_other = len(self.other_list)
        self.n_train = len(self.train_list)

    def __len__(self):
        return self.max_contrast + self.n_other + self.n_train

    def __getitem__(self, idx):
        if idx < self.max_contrast:
            image = v2.functional.pil_to_tensor(
                self.contrast[idx]["image"]
            )
            is_train = False
        elif idx < self.max_contrast + self.n_other:
            img_path = self.other_list[idx - self.max_contrast]
            image = decode_image(img_path)
            is_train = False
        else:
            img_path = self.train_list[idx - self.max_contrast - self.n_other]
            image = decode_image(img_path)
            is_train = True

        num_objs = 1
        _, h, w = image.shape
        boxes = torch.zeros((num_objs, 4), dtype=torch.float)
        boxes[0, 0] = math.floor(w * 0.1)
        boxes[0, 1] = math.floor(h * 0.1)
        boxes[0, 2] = math.floor(w * 0.9)
        boxes[0, 3] = math.floor(h * 0.9)

        if is_train:
            labels = torch.ones((num_objs,), dtype=torch.int64)
        else:
            labels = torch.zeros((num_objs,), dtype=torch.int64)
        area = (boxes[:, 3] - boxes[:, 1]) * (boxes[:, 2] - boxes[:, 0])
        target = {}
        target["boxes"] = torchvision.tv_tensors.BoundingBoxes(
            boxes, format="XYXY", canvas_size=(h, w)
        )

        target["masks"] = tv_tensors.Mask(masks)
        target["labels"] = labels
        target["image_id"] = idx
        target["area"] = area

        if self.transforms is not None:
            image, target = self.transforms(image, target)
        return image, target


class MMRVideos(Dataset):
    def read_files(self):
        frame_store = []
        last_frame = []
        for video in (self.root / Path("train")).iterdir():
            frames = sorted([str(frame) for frame in video.glob("*.png")])
            frame_store += frames
            last_frame += [False] * (len(frames) - 1) + [True]
        self.frame_store = frame_store
        self.last_frame = last_frame
        self.frame_offset = list(itertools.accumulate(last_frame))
        self.max_id = len(self)

    def __init__(self, root: Path, transform=None):
        self.root = root
        self.transform = transform
        self.read_files()

    def __len__(self):
        return len(self.frame_store) - self.frame_offset[-1]

    def __getitem__(self, lidx):
        idx = lidx + self.frame_offset[lidx]
        img_path = self.frame_store[idx]
        image = decode_image(img_path)

        if not self.last_frame[idx] and idx < self.max_id - 1:
            nx_frame = decode_image(self.frame_store[idx + 1])
        else:
            nx_frame = None
        if self.transform:
            image = self.transform(image)
            if nx_frame is not None:
                nx_frame = self.transform(nx_frame)
        return image, nx_frame
