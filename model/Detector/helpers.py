import matplotlib.pyplot as plt
from typing import Dict, List, Tuple
import torch
from torchvision.utils import draw_bounding_boxes, draw_segmentation_masks
from torchvision import tv_tensors
from torchvision.transforms import v2
from torchvision.transforms.v2 import functional as F
import torchvision

plt.rcParams["savefig.bbox"] = "tight"

def draw_keypoints(image: torch.Tensor, keypoints: torch.Tensor, **kwargs) -> torch.Tensor:
    if not isinstance(image, torch.Tensor):
        raise TypeError(f"The image must be a tensor, got {type(image)}")
    elif not (image.is_floating_point() or image.dtype == torch.uint8) :
        raise ValueError(f"The image dtype must be uint8 or float, got {image.dtype}")
    elif image.dim() != 3:
        raise ValueError("Pass individual images, not batches")
    elif keypoints.dim() !=3:
        raise ValueError(f"Expected Keypoints of shape (num_instances, K, 2), not {keypoints.shape}")
    if image.shape[0] == 1:
        img = F.grayscale_to_rgb(image)
    else:
        img = image
    col = kwargs.get('colors','red')
    return torchvision.utils.draw_keypoints(img, keypoints, colors=col, radius=3)

def show(imgs: List[torch.Tensor]|torch.Tensor):
    if not isinstance(imgs, list):
        imgs = [imgs]
    fig, axs = plt.subplots(ncols=len(imgs), squeeze=False, figsize=(14, 6))
    for i, img in enumerate(imgs):
        if img is None:
            continue
        img = img.detach()
        img = tvF.to_pil_image(img, mode='RGB')#, mode='F')
        axs[0, i].imshow(img)#np.asarray(img) cmap='gray')
        axs[0, i].set(xticklabels=[], yticklabels=[], xticks=[], yticks=[])
    fig.show()

def visualize_centroids(image: torch.Tensor, centroids: torch.Tensor) -> torch.Tensor:
    match image.shape:
        case (1,_,_):
            img = F.grayscale_to_rgb(image.detach())
        case (3,_,_):
            img = image.copy().detach()
        case _:
            raise ValueError(f"Expected image to be of type grayscale or RGB, got {image.shape}")
    if centroids.dim() != 3 or centroids.shape[-1] != 2:
        raise ValueError(f"centroids need to be of shape (N,1,2), got {centroids.shape}")
    return draw_keypoints(image, torch.unique(centroids, dim=0))
def _generate_color_palette(num_objects: int):
    palette = torch.tensor([2**25 - 1, 2**15 - 1, 2**21 - 1])
    return [tuple((i * palette) % 255) for i in range(num_objects)]

@torch.no_grad()
def test_decom_draw_segmentation_masks(image: torch.Tensor, masks: torch.Tensor,alpha: float = 0.8, colors=None, mask_threshold: float = 0.5)-> torch.Tensor:
    """
    Rewrite of the pytorch version to accept greyscale images. Outputs RGB.
    Maybe it can be removed
    """
    if not isinstance(image, torch.Tensor):
        raise TypeError(f"The image must be a tensor, got {type(image)}")
    elif not (image.is_floating_point() or image.dtype == torch.uint8):
        raise ValueError(f"The image dtype must be uint8 or float, got {image.dtype}")
    elif image.dim() != 3:
        raise ValueError("Pass individual images, not batches")
    if masks.ndim == 2:
        masks = masks[None, :, :]
    if masks.ndim != 3:
        raise ValueError("masks must be of shape (H, W) or (batch_size, H, W)")
    if not (masks.dtype == torch.bool or not (masks.is_floating_point() and masks.max()<=1.0)):
        raise ValueError(f"The masks must be of dtype bool. Got {masks.dtype}")
    if masks.shape[-2:] != image.shape[-2:]:
        raise ValueError(f"The image and the masks must have the same height and width. Got {image.shape[-2:]} and {masks.shape[-2:]}.")
    if masks.is_floating_point():
        masks = masks >= mask_threshold
    num_masks = masks.size()[0]
    overlapping_masks = masks.sum(dim=0) > 1

    if num_masks == 0:
        warnings.warn("masks doesn't contain any mask. No mask was drawn")
        return image
    original_dtype = image.dtype
    colors = [#TODO make it such 0-255 is int and 0-1 is float
        torch.tensor(color, dtype=original_dtype, device=image.device)
        for color in _generate_color_palette(num_masks)
    ]
    if image.size()[0] == 1:
        img_to_draw = F.grayscale_to_rgb(image.detach().clone())
    elif image.size()[0] == 3:
        img_to_draw = image.detach().clone()
    else:
        raise ValueError("Pass a float greyscale image. Other Image formats are not supported")
    # TODO: There might be a way to vectorize this
    for mask, color in zip(masks, colors):
        img_to_draw[:, mask] = color[:, None]

    img_to_draw[:, overlapping_masks] = 0

    out = image.clone() * (1 - alpha) + img_to_draw * alpha
    # Note: at this point, out is a float tensor in [0, 1] or [0, 255] depending on original_dtype
    return out.to(torch.uint8)#to(original_dtype) hardcode the image format to [0,255]

@torch.no_grad()
def viz_dataset(image: torch.Tensor|Tuple, target: Dict=None, kpts: List|torch.Tensor=None, color='red') -> torch.Tensor:
    img = None
    mask = boxes = None
    mres = bres = None
    if isinstance(image, tuple):
        img, target = image
        img = img.detach().clone()
    else:
        img = image.detach().clone()
    if img.dim() == 4 and img.shape[0]==1:
        img = img[0]
    if target is not None:
        mask = target.get('mask')
        boxes = target.get('bbox')
    if img.max().item() > 1.0:
        img = img.to(torch.uint8)
    if img.shape[0] == 1:
        img = F.grayscale_to_rgb(img)
    assert img.dim() == 3 and img.shape[0] == 3, img.shape
    if mask is not None:
        mres = draw_segmentation_masks(img, mask, alpha=0.8)
    if boxes is not None:
        bres = draw_bounding_boxes(img, boxes, width=2)
        #y_centers = torch.stack(((boxes[:,0]+boxes[:,2])/2, (boxes[:,1]+boxes[:,3])/2)).T.reshape((-1,1,2))
        #bres = draw_keypoints(bres, y_centers)
    kpts_vis = []
    #img_to_draw = img
    if isinstance(kpts, torch.Tensor):
        kpts_vis.append(draw_keypoints(img, kpts, colors=color))
    #elif isinstance(kpts, list):
    #    for i in kpts:temp remove
    #        kpts_vis.append(draw_keypoints(img_to_draw, i, colors=color))
    out = [mres, bres, *kpts_vis]
    return [x for x in out if x is not None]

def test_decom_plot(imgs, row_title=None, bbox_width=3, **imshow_kwargs):
    if not isinstance(imgs, list):
        # Make a 2d grid even if there's just 1 row
        imgs = [imgs]

    num_rows = len(imgs)
    num_cols = 1#num_cols = len(imgs[0])
    _, axs = plt.subplots(nrows=num_rows, ncols=num_cols, squeeze=False)
    for row_idx, img in enumerate(imgs):
        #for col_idx, img in enumerate(row):
            boxes = None
            masks = None
            if isinstance(img, tuple):
                image, target = img
                image = F.to_image(image)
                if isinstance(target, dict):
                    boxes = target.get("boxes")
                    masks = target.get("masks")
                    print("visualizing with boxes and masks")
                elif isinstance(target, tv_tensors.BoundingBoxes):
                    boxes = target
                    # Conversion necessary because draw_bounding_boxes() only
                    # work with this specific format.
                    if tv_tensors.is_rotated_bounding_format(boxes.format):
                        boxes = v2.ConvertBoundingBoxFormat("xyxyxyxy")(boxes)
                else:
                    raise ValueError(f"Unexpected target type: {type(target)}")
            elif isinstance(img, torch.Tensor):
                image = F.to_image(img)
            else:
                raise ValueError(f"Unexpected target type: {type(img)}")
            if image.dtype.is_floating_point and image.min() < 0:
                # Poor man's re-normalization for the colors to be OK-ish. This
                # is useful for images coming out of Normalize()
                image -= image.min()
                image /= image.max()

            image = F.to_dtype(image, torch.uint8, scale=True)
            if boxes is not None:
                image = draw_bounding_boxes(image, boxes, colors="yellow", width=bbox_width)
            if masks is not None:
                image = draw_segmentation_masks(image, masks.to(torch.bool), colors=["red"] * masks.shape[0], alpha=.65)

            ax = axs[row_idx, 0]
            ax.imshow(image.permute(1, 2, 0).numpy(), **imshow_kwargs)
            ax.set(xticklabels=[], yticklabels=[], xticks=[], yticks=[])

    if row_title is not None:
        for row_idx in range(num_rows):
            axs[row_idx, 0].set(ylabel=row_title[row_idx])

    plt.tight_layout()
