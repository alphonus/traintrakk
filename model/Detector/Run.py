import torch
import torch.nn.functional as F
import torchvision
from torchvision import tv_tensors

from typing import List
from sklearn.cluster import AgglomerativeClustering

def merge_kypts_fields(points:tv_tensor.KeyPoints, fields:tv_tensor.Image) -> tv_tensor.KeyPoints:
    """v2.functional.clamp_keypoints(
    """
    return torchvision.transforms.v2.functional.clamp_keypoints(tv_tensors.wrap(points+torch.flip(fields, (2,)), like=points))

def process_centers(points: torchvision.tv_tensor.KeyPoints, max_dist:float=0.1) -> torch.Tensor:
    """
    Get the centercandidates of a prediction.
    """
    points = torchvision.transforms.v2.functional.clamp_keypoints(points)
    H,W = points.canvas_size
    _max_dist = max(H,W)*max_dist
    B, N ,_ = keypoints.shape
    if keypoints.shape != (B,N,2):
        raise RuntimeError( f"Got {keypoints.shape}")
    #dist = torch.cdist(points, points, p=p)
    np_points = points.detach().numpy()
    centroids = []
    for b in range(B):
        cluster = AgglomerativeClustering(linkage='ward', distance_threshold=_max_dist, n_clusters=None).fit(np_points[b])
        n_clusters = max(cluster.labels_)
        for n in range(n_clusters):
            centroids.append(points[b,cluster.labels_ == n,:].mean(dim=0))
    out = tv_tensors.wrap(torch.stack(centroids), like=points)
    if out.shape != (B,1,2):
        raise RuntimeError( f"Got {out.shape}")
    return out
