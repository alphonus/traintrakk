#!/usr/bin/env python
# coding: utf-8

# # Initial setup
# setup of the Dataset classes


import json
import os.path
from pathlib import Path
from typing import Dict, List, Tuple
import math
import copy
import random

import cv2
import numpy as np
import itertools
# from pytorch example:https://docs.pytorch.org/tutorials/intermediate/transformer_building_blocks.html#the-above-building-blocks-are-all-you-need-as-of-october-2024
# modified to make query and value project identically:TODO
import torch
import torchvision
from datasets import load_dataset
from scipy.interpolate import CloughTocher2DInterpolator, LinearNDInterpolator
from torch.profiler import record_function
from torch.utils.data import Dataset
from torchvision import tv_tensors
from torchvision.io import decode_image
from torchvision.transforms import v2
from torchvision.ops import masks_to_boxes
from torch.distributions.normal import Normal

from .zoo.SuperPointPretrainedNetwork.demo_superpoint import SuperPointNet


def process_json_annotations(filename: str, imgroot: Path) -> List:
    """reads a via generated json annotation file to convert to individual masks."""
    masks = {}
    bboxes = {}
    with open(filename, encoding="utf-8") as fileptr:
        dump = json.load(fileptr)
        if '_via_img_metadata' in dump.keys():
            dump = dump['_via_img_metadata']
    file_struct = {"filename", "size", "regions", "file_attributes"}
    for k in dump.keys():
        assert set(dump[k].keys()) <= file_struct, f"File format err, got{set(dump.keys())}"
    for k, image in dump.items():
        rects = list(
            filter(lambda x: x["shape_attributes"]["name"] == "rect", image["regions"])
        )
        n_trains = int(image["file_attributes"]["n_trains"])
        assert n_trains == len(
            rects
        ), f"length mismatch in {k}. expected{n_trains}, got {len(rects)}"
        #img_size = get_img_size()
        im = cv2.imread(imgroot / image["filename"])
        H, W, C = im.shape
        masks[image["filename"]], bboxes[image["filename"]] = gen_mask(image["regions"], (H, W), n_trains)
    return masks, bboxes


@torch.no_grad()
def gen_mask(
    regions: List[Dict], image_size: Tuple[int], n_trains: int, cutoff=0.1
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
    H,W = image_size
    #h_grid = torch.arange(0,H,1)
    #w_grid = torch.arange(0,W,1)
    #mask = torch.zeros((n_trains, H, W), dtype=torch.float)#from bool
    mask = []
    #Y, X = np.meshgrid(np.arange(0,H,1), np.arange(0,W,1))
    #blurrer = v2.GaussianBlur(kernel_size=(11, 1), sigma=(5., 5.))
    boxes = []
    for i in range(n_trains):
        bbox = bboxs[i]["shape_attributes"]
        x0, y0, width, height = bbox["x"], bbox["y"], bbox["width"], bbox["height"]
        centroid = (y0 + height/2, x0 + width/2)
        boxes.append([x0, x0 + width, y0, y0+height])  #XYXY
        #set sigma as 2* bbox max dim as a ration of image dim
        sigma = float(max(H,W))
        #h_dist = torch.exp(Normal(torch.tensor([y0+height/2]), torch.tensor([sigma])).log_prob(h_grid))
        # 1.0-abs(p-centroid[0])/sigma
        h_dist = torch.tensor([max(0.0, 1.0 - abs(p - centroid[0]) / sigma) * 0.5 for p in range(H)])
        w_dist = torch.tensor([max(0.0, 1.0 - abs(p - centroid[1]) / sigma) * 0.5 for p in range(W)])
        #w_dist = torch.exp(Normal(torch.tensor([x0+width/2]), torch.tensor([sigma])).log_prob(w_grid))
        centr_map = torch.outer(h_dist, w_dist)
        assert centr_map.shape == (H, W), centr_map.shape
        assert centr_map.dtype == torch.float, centr_map.dtype
        #assert centr_map.amin()>= 0.0 and centr_map.amax() <= 1.0 and centr_map.amax() > 0.9, (centr_map.max(), centr_map.min())
        #mask[i] = centr_map.detach().clone()

        points = []
        values = []
        for point in sorted_points[i]:
            posx = float(point["shape_attributes"]["cx"])
            posy = float(point["shape_attributes"]["cy"])
            label = float(point["region_attributes"]["entity"] == "train")
            points.append((posy,posx))
            values.append(label)
        points = np.array(points)
        values = np.array(values)
        assert values.min() >= 0.0 and values.max() <= 1.0, "Values out of range [0,1]"
        interp = LinearNDInterpolator(points, values, fill_value=0.0)#, fill_value=0.0 TEST if biasing the bbox helps

        X = np.arange(x0, x0 + width, 1, dtype=np.float32)# rewrite to bias the whole image
        Y = np.arange(y0, y0 + height, 1, dtype=np.float32)
        Y, X = np.meshgrid(Y, X)
        Z = torch.tensor(interp(Y,X).T) #> cutoff
        assert Z.size() == (height, width), f"Got ({Z.shape}, expected: {(height, width)})"
        assert Z.max() < 1.1, f"Z max larger 1, is {Z.max()}, min: {Z.min()}"
        assert (Z > cutoff).any(), f"No mask created for train {i}, Y:{Y.shape},X:{X.shape}, Z:{Z.shape}"
        centr_map[y0: y0 + height, x0: x0 + width] = torch.clamp(Z, min=0.0, max=1.0).detach().clone()
        mask.append(centr_map.detach().clone())
    mask = torch.clamp(torch.stack(mask), min=0.0, max=1.0)
    assert not torch.isnan(mask).any()
    assert mask.shape == (n_trains, H, W)
    assert mask.amax(dim=(1,2)).size(dim=0) == n_trains and (mask.amax(dim=(1,2))>cutoff).all(), f"Shape: {mask.amax(dim=(1,2)).size(dim=0)}, Num Trains:{n_trains}, Err: {(mask.amax(dim=(1,2))>cutoff)}"
    return mask, torch.tensor(boxes)


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
    return (xs,ys), heatmap
    
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
    """

        target is of type dict and stores the different true values.
        target['mask']: (N_Batch, Height, Width), float 0-1 if there is a train present.
        target['fields']: (2, Height, Width), int, The closest centroid vector from each pixel. ToBe found out which channel of dim 0 ist height and width.
    """

    def __init__(self, root: Path, image_transforms=None, target_transforms=None, transforms=None, interpolation_threshold=130, debug=False):
        self.debug = debug
        self.field_scale_unit = 0.1 # check if a mean value of 1.1 of the field vectors is good.
        if isinstance(root, str):
            self.root = Path(root)
        elif isinstance(root, Path):
            self.root = root
        self.transforms = transforms
        self.image_transforms = image_transforms
        self.target_transforms = target_transforms
        self.mask_thresh = 0.3
        self._load_annotations("data/model_trains.json")
        with record_function("interp_masks"):
            self._interp_masks(interpolation_threshold=interpolation_threshold)
        with record_function("calc_centroid"):
            self._calc_centroids()
        self._calc_fields()
        self.n_examples = len(self.labeldimages)
        # print(self.masks['woodbridge_191.png'][0].max())

    def _load_annotations(self, filename:str):
        """Load prelabeled training data.
        """
        self.targets = {}
        self.prelabled_images = []
        with open(filename, encoding="utf-8") as fileptr:
            dump = json.load(fileptr)
        if '_via_img_metadata' in dump.keys():
            dump = dump['_via_img_metadata']
        file_struct = {"filename", "size", "regions", "file_attributes"}

        for k, image in dump.items():
            img_data = {}
            assert set(dump[k].keys()) <= file_struct, f"File format err, got{set(dump.keys())}"
            rects = list(
                filter(lambda x: x["shape_attributes"]["name"] == "rect", image["regions"])
            )
            n_trains = int(image["file_attributes"]["n_trains"])
            assert n_trains == len(rects), f"length mismatch in {k}. expected{n_trains}, got {len(rects)}"
            #img_size = get_img_size()
            im = cv2.imread(self.root / image["filename"])
            H, W, C = im.shape
            img_data['img_meta'] = (n_trains,H,W)
            img_data['mask'], img_data['bbox'] = gen_mask(image["regions"], (H, W), n_trains)
            self.targets[image["filename"]] = copy.deepcopy(img_data)
            self.prelabled_images.append(image["filename"])
        self.prelabled_images = sorted(self.prelabled_images.copy())

    @torch.no_grad()
    def _interp_masks(self, interpolation_threshold):
        """
        Assumes that original images have sequential file names.
        [videoname]_[number].png
        """
        self.labeldimages = self.prelabled_images.copy()
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
            source = self.targets[cur_img]
            final = self.targets[next_img]
            if source['img_meta'] != final['img_meta']:
                print("Loss of Number trains, skipping")
                continue
            source_img = source['mask']
            source_box = source['bbox']
            if final['mask'].shape[0] != source_img.shape[0]:
                # Todo interpt across varying masks number
                continue
            spacing = len(inter_frames) + 1
            img_diff = (final['mask'] - source_img) / spacing
            box_diff = (final['bbox'] - source_box) / spacing
            N, H, W = source_img.shape
            with record_function("iter_steps"):
                for step in range(1, spacing):
                    img_data = {}
                    img_data['mask'] = torch.clamp(source_img + img_diff * step, min=0.0, max=1.0)
                    img_data['bbox'] = source_box + box_diff * step
                    img_data['img_meta'] = (N, H, W)
                    self.targets[inter_frames[step - 1]] = copy.deepcopy(img_data)
                    self.labeldimages.append(inter_frames[step - 1])
            self.labeldimages = sorted(self.labeldimages)

    @torch.no_grad()
    def _calc_centroids(self, mode:str='bbox'):
        """
        Calculate centroid for each entity. Either with mask mean or bbox center
        """
        if mode not in ['bbox', 'mask']:
            raise RuntimeWarning(f"Selected mode {mode} is not supported, switching to bbox")
        for img_id in self.labeldimages:
            if mode == 'bbox':
                # get for each image the bbox
                # calc centroid
                # add centroids to img_data target
                boxes = self.targets[img_id]['bbox'] # (N,4) XXYY
                X,Y = (boxes[:,0]+boxes[:,1])/2, (boxes[:,2]+boxes[:,3])/2
                # centroids = torch.stack((X,Y)) # (2,N)
                centroids = torch.stack((X,Y)).T # (N,2)
                assert centroids.shape[0] == self.targets[img_id]['img_meta'][0], f"got {centroids.shape[0]}, expected {self.targets[img_id]['img_meta'][0]}"
                self.targets[img_id]['centroids'] = centroids.clone()
            elif mode == 'mask':
                raise NotImplementedError(f"Selected mode {mode} is not implemented")
            else:
                raise RuntimeError("Wrong Exec Path")
    @staticmethod
    def get_maskid_lookup(mask):
        """
        creates an reverse lookup table for pixel to mask id
        """
        N,H,W = mask.shape
        b = torch.nonzero(mask)
        out = torch.full((H,W), -1, dtype=int)
        for n in range(N):
            out[b[b[:,0]==n,1:3]] = n
        return out

    @staticmethod
    def _gen_field(img_dim:Tuple[int,int,int], centroid:Tuple[int,int]) -> torch.Tensor:
        """
        Generate an attraction field for a centroid.
        img_dim: (H,W)
        centroid: (X,Y)
        return Tensor (N,H,W,2)
        """
        N,H,W = img_dim
        y_index = torch.arange(H, dtype=torch.int)
        x_index = torch.arange(W, dtype=torch.int)
        vector_field = torch.cartesian_prod(y_index, x_index).reshape(H, W, 2)
        vector_field = vector_field.repeat(N,1,1,1)
        #cntr = torch.tensor((centroid[1], centroid[0]))
        #cntr_field = torch.flip(centroid, (1,))[:,None,None,:].repeat(1,H,W,1)
        cntr_field = centroid[:,None,None,:].repeat(1,H,W,1)
        return torch.sub(cntr_field, vector_field)

    @staticmethod
    def norm_fields(fields, step_unit) -> torchvision.tv_tensors.Image:
        """
        args
            fields: Tensor (H,W,2)
        return Tensor (2,H,W)
        """
        if fields.dim() != 3:
            raise AttributeError("Need 3D Tensor")
        if step_unit.shape != (2,):
            raise AttributeError(f"Norming unit is not a unit for each dim, got {step_unit.shape}")
        out_field = torch.div(fields, step_unit)
        return torchvision.tv_tensors.Image(torch.movedim(out_field,(0,1,2),(1,2,0)))

    @torch.no_grad()
    def _calc_fields(self, treshold:float=0.3):
        """
        uses the centroids to create a basic attraction field for each pixel.
        Overrites with mask attraction.
        """
        #TODO rewite to dim:(2,H,W)
        if treshold < 0.0 or treshold > 1.0:
            treshold = 0.3
            raise UserWarning("Treshold set out of bounds, defaulting to 0.3")
        for image_id in self.labeldimages:
            target = self.targets[image_id]
            N, H, W = target['img_meta']
            STEP_UNIT = torch.Tensor([H*self.field_scale_unit, W*self.field_scale_unit])
            field = self._gen_field(target['img_meta'], target['centroids'])
            assert field.shape == (N,H,W,2)

            b = torch.linalg.vector_norm(field, dim=3)
            b = torch.argmin(b, 0)

            idx_mask = target['mask'] >= treshold
            raw_mask = target['mask'].amax(dim=0) # lower the agressivemess
            assert raw_mask.shape == (H,W)
            assert idx_mask.shape == (N,H,W)
            for n in range(N):
                b[idx_mask[n]] = n
            # TODO make is such b also gets the indexes from the mask as overrites
            out_field = torch.zeros((H,W,2))
            for n in range(N):
                #tmp_pmask = field[n, b == n & idx_mask[n]]
                #out_field[b == n & idx_mask[n]] = tmp_pmask
                #tmp_nmask = field[n, b == n & ~idx_mask[n]]
                #tmp_nmask *= 0.4
                #out_field[b == n & ~idx_mask[n]] = tmp_nmask
                out_field[b == n] = field[n, b == n]

            assert out_field.shape == (H,W,2)

            out_field = torch.mul(out_field, raw_mask[:,:,None])
            self.targets[image_id]['fields'] = self.norm_fields(out_field, STEP_UNIT)

    def __len__(self):
        return self.n_examples

    def __getitem__(self, idx):
        img_nameid = self.labeldimages[idx]
        img_path = self.root / img_nameid
        image = tv_tensors.Image(decode_image(img_path, mode='RGB'))
        target = {}
        loc_target = self.targets[img_nameid]
        mask = tv_tensors.Mask(loc_target['mask'] >= self.mask_thresh)  # .max(axis=0).values

        if self.debug:
            target["image_id"] = img_nameid
            target['mask'] = mask
            target['centroid'] = tv_tensors.KeyPoints(loc_target['centroids'], canvas_size=mask.shape[-2:])
            target['bbox'] = tv_tensors.BoundingBoxes(masks_to_boxes(mask), format=tv_tensors.BoundingBoxFormat.XYXY, canvas_size=mask.shape[-2:])
        else:
            target['mask'] = torch.amax(mask, 0, keepdim=True) #.unsqueeze(0)
        #target['mask'] = mask
        target["fields"] = loc_target['fields']#.unsqueeze(0)
        #target["masks"] = torchvision.tv_tensors.Mask(self.masks[img_nameid])
        if self.image_transforms:
            image = self.image_transforms(image)
        if self.target_transforms:
            target = self.target_transforms(target)
        if self.transforms:
            image, target = self.transforms(image, target)
            #target['mask'] = self.transforms(target['mask'])
            #target['fields'] = self.transforms(target['fields'])
            #target['bbox'] = self.transforms(target.get('bbox'))
        return image, target

class MMRFineTune(Dataset):
    @staticmethod
    def istrain(path: Path) -> bool:
        return path.parts[-2].contains("train")

    def __init__(self, root: Path, transforms=None):
        if isinstance(root, str):
            self.root = Path(root)
        elif isinstance(root, Path):
            self.root = root
        self.transforms = transforms
        self.other_list = list(self.root.glob("other/*.jpg"))
        self.train_list = list(self.root.glob("train/*.jpg"))
        ds = load_dataset("zh-plus/tiny-imagenet", split='train')
        self.contrast = ds
        self.max_contrast = 100  # max num of contrast samples
        contrast_train_mask = list(map(lambda x: x==75 or x==95, ds['label']))
        self.contrast_train_idx = [i for i,x in enumerate(contrast_train_mask) if x]
        self.contrast_other_idx = [i for i,x in enumerate(contrast_train_mask) if not x]#RANDOM IDX from ds
        self.contrast_train_idx = random.sample(self.contrast_train_idx, self.max_contrast)
        self.contrast_other_idx = random.sample(self.contrast_other_idx, self.max_contrast)
        self.n_other = len(self.other_list)
        self.n_train = len(self.train_list)

    def __len__(self):
        return self.max_contrast*2 + self.n_other + self.n_train

    def __getitem__(self, idx):
        if idx < self.max_contrast:
            masked_idx = self.contrast_other_idx[idx]
            with record_function("get_contrast"):
                image = v2.functional.pil_to_tensor(
                    self.contrast[masked_idx]['image']
                )
            is_train = False
        elif idx < self.max_contrast*2:
            masked_idx = self.contrast_train_idx[idx - self.max_contrast]
            with record_function("get_contrast"):
                image = v2.functional.pil_to_tensor(
                    self.contrast[masked_idx]['image']
                )
            is_train = True
        elif idx < self.max_contrast*2 + self.n_other:
            img_path = self.other_list[idx - self.max_contrast*2]
            image = decode_image(img_path)
            is_train = False
        else:
            img_path = self.train_list[idx - self.max_contrast*2 - self.n_other]
            image = decode_image(img_path)
            is_train = True

        num_objs = 1
        _, h, w = image.shape

        if is_train:
            labels = 1#torch.ones((num_objs,), dtype=torch.int64)
        else:
            labels = 0#torch.zeros((num_objs,), dtype=torch.int64)
        #area = (boxes[:, 3] - boxes[:, 1]) * (boxes[:, 2] - boxes[:, 0])
        target = {}
        #target["boxes"] = tv_tensors.BoundingBoxes(
        #    boxes, format="XYXY", canvas_size=(h, w)
        #)

        #target["masks"] = tv_tensors.Mask(masks)
        target["labels"] = labels
        target["image_id"] = idx
        #target["area"] = area
        with record_function("transform"):
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
