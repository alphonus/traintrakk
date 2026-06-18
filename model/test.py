from typing import List, Any, ClassVar, Optional, Sequence, Tuple
import unittest
import torch
import torchvision
from torchvision.tv_tensors import Image, KeyPoints
from Data import MMRPifPafTune
test_tensors = {
            '2x5x5': ((2, 5, 5), torch.Tensor([ # two masks
                [[0.9,1.0,1.0,0.4,0.0],
                 [1.0,1.0,1.0,0.4,0.0],
                 [1.0,1.0,1.0,0.4,0.0],
                 [0.4,0.5,0.4,0.0,0.0],
                 [0.0,0.0,0.0,0.0,0.0]],
                [[0.0,0.0,0.0,0.0,0.0],
                 [0.0,0.0,0.0,0.0,0.0],
                 [0.0,0.9,0.9,0.9,0.9],  # should overwrite the other assignemtn
                 [0.0,0.9,1.0,1.0,0.9],
                 [0.0,0.9,1.0,0.9,0.7]]
                ])),
            '1x5x4': ((1, 5, 4), torch.Tensor([ # two masks
                [[0.9,1.0,1.0,0.4],
                 [1.0,1.0,1.0,0.4],
                 [1.0,1.0,1.0,0.4],
                 [0.4,0.5,0.4,0.0],
                 [0.0,0.0,0.0,0.0]],
                ]))
            }
class TestDataProcessing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.normed_fields = {
            '1centrx5x5' : torch.tensor([ # centroid at (1,1)
                [[2.0, 2.0, 2.0, 2.0, 2.0], #h dim
                 [0.0, 0.0, 0.0, 0.0, 0.0],
                 [-2.0,-2.0,-2.0,-2.0,-2.0],
                 [-4.0,-4.0,-4.0,-4.0,-4.0],
                 [-6.0,-6.0,-6.0,-6.0,-6.0]],
                 [[2.0,0.0,-2.0,-4.0,-6.0], # w dim
                 [2.0,0.0,-2.0,-4.0,-6.0],
                 [2.0,0.0,-2.0,-4.0,-6.0],
                 [2.0,0.0,-2.0,-4.0,-6.0],
                 [2.0,0.0,-2.0,-4.0,-6.0]]
                ]),
                '1centrx5x4' : torch.tensor([ # centroid at (1,1)
                [[2.0, 2.0, 2.0, 2.0], #h dim
                 [0.0, 0.0, 0.0, 0.0],
                 [-2.0,-2.0,-2.0,-2.0],
                 [-4.0,-4.0,-4.0,-4.0],
                 [-6.0,-6.0,-6.0,-6.0]],
                 [[2.5,0.0,-2.5,-5.0], # w dim
                 [2.5,0.0,-2.5,-5.0],
                 [2.5,0.0,-2.5,-5.0],
                 [2.5,0.0,-2.5,-5.0],
                 [2.5,0.0,-2.5,-5.0]]
                ]),
                 '2centrx5x5' : torch.tensor([
                [[4.,4.,4.,4.,4.],
                 [2.,2.,2.,2.,2.],
                 [0.,0.,0.,0.,0.],
                 [-2.0,-2.0,-2.0,-2.0,-2.0],
                 [-4.0,-4.0,-4.0,-4.0,-4.0]],
                [[3.0,1.0,-1.0,-3.0,-5.0],
                 [3.,1.,-1.,-3.,-5.],
                 [3.0,1.0,-1.0,-3.0,-5.0],
                 [3.0,1.0,-1.0,-3.0,-5.0],
                 [3.0,1.0,-1.0,-3.0,-5.0]
                    ]]),
            }
        cls.aggregated_fields = {
            '1centrx5x5' : torch.tensor([
                [[ 1.,  1.], [ 1.,  0.], [ 1., -1.], [ 1., -2.], [ 1., -3.]], # centroid (1,1)
                [[ 0.,  1.],[ 0.,  0.], [ 0., -1.], [ 0., -2.], [ 0., -3.]],
                [[-1.,  1.], [-1.,  0.], [-1., -1.], [-1., -2.], [-1., -3.]],
                [[-2.,  1.],  [-2.,  0.], [-2., -1.],  [-2., -2.], [-2., -3.]],
                [[-3.,  1.], [-3.,  0.],  [-3., -1.],  [-3., -2.],  [-3., -3.]],
               ]),
            '1centrx5x4' : torch.tensor([
                [[ 1.,  1.], [ 1.,  0.], [ 1., -1.], [ 1., -2.]], # centroid (1,1)
                [[ 0.,  1.],[ 0.,  0.], [ 0., -1.], [ 0., -2.]],
                [[-1.,  1.], [-1.,  0.], [-1., -1.], [-1., -2.]],
                [[-2.,  1.],  [-2.,  0.], [-2., -1.],  [-2., -2.]],
                [[-3.,  1.], [-3.,  0.],  [-3., -1.],  [-3., -2.]],
               ]),
            '2centrx5x5' : torch.tensor([
                [[2., 1.5],  [2, 0.5], [2.,-0.5], [2.,-1.5], [2.,-2.5]],
                [[1., 1.5],  [1., 0.5], [1.,-0.5], [1.,-1.5], [1.,-2.5]],
                [[0., 1.5],  [0., 0.5], [0.,-0.5], [0.,-1.5], [0.,-2.5]],
                [[-1., 1.5], [-1., 0.5], [-1.,-0.5], [-1.,-1.5], [-1.,-2.5]],
                [[-2., 1.5], [-2., 0.5], [-2.,-0.5], [-2.,-1.5], [-2.,-2.5]],
                ]),
            }
        cls.raw_fields = {
            '1centrx5x5' : torch.tensor([
               [[[ 1.,  1.], [ 1.,  0.], [ 1., -1.], [ 1., -2.], [ 1., -3.]], # centroid (1,1)
                [[ 0.,  1.],[ 0.,  0.], [ 0., -1.], [ 0., -2.], [ 0., -3.]],
                [[-1.,  1.], [-1.,  0.], [-1., -1.], [-1., -2.], [-1., -3.]],
                [[-2.,  1.],  [-2.,  0.], [-2., -1.],  [-2., -2.], [-2., -3.]],
                [[-3.,  1.], [-3.,  0.],  [-3., -1.],  [-3., -2.],  [-3., -3.]]],
               ]),
            '1centrx5x4' : torch.tensor([
               [[[ 1.,  1.], [ 1.,  0.], [ 1., -1.], [ 1., -2.]], # centroid (1,1)
                [[ 0.,  1.],[ 0.,  0.], [ 0., -1.], [ 0., -2.]],
                [[-1.,  1.], [-1.,  0.], [-1., -1.], [-1., -2.]],
                [[-2.,  1.],  [-2.,  0.], [-2., -1.],  [-2., -2.]],
                [[-3.,  1.], [-3.,  0.],  [-3., -1.],  [-3., -2.]]],
               ]),
            '2centrx5x5' : torch.tensor([
               [
                [[ 1.,  1.], [ 1.,  0.], [ 1., -1.], [ 1., -2.], [ 1., -3.]], # centroid (1,1)
                [[ 0.,  1.],[ 0.,  0.], [ 0., -1.], [ 0., -2.], [ 0., -3.]],
                [[-1.,  1.], [-1.,  0.], [-1., -1.], [-1., -2.], [-1., -3.]],
                [[-2.,  1.],  [-2.,  0.], [-2., -1.],  [-2., -2.], [-2., -3.]],
                [[-3.,  1.], [-3.,  0.],  [-3., -1.],  [-3., -2.],  [-3., -3.]]],
                [[[ 3.,  2.], [ 3.,  1.], [ 3., 0.], [ 3., -1.], [ 3., -2.]], # centroid (3,2)
                [[ 2.,  2.], [ 2.,  1.], [ 2.,  0.], [ 2., -1.], [ 2., -2.]],
                [[ 1.,  2.], [ 1.,  1.], [ 1.,  0.], [ 1., -1.], [ 1., -2.]],
                [[ 0.,  2.],  [ 0.,  1.], [ 0.,  0.],  [ 0., -1.], [ 0., -2.]],
                [[-1.,  2.], [-1.,  1.], [-1., 0.], [-1., -1.], [-1., -2.]]]
                ]),
            }
        cls.large_fields = {
            '1centrx5x5' : Image([ # centroid at (2,2)
                [[2.0, 2.0, 2.0, 2.0, 2.0,2.0, 2.0, 2.0, 2.0, 2.0], #h dim
                 [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
                 [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                 [-1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0],
                 [-2.0,-2.0,-2.0,-2.0,-2.0,-2.0,-2.0,-2.0,-2.0,-2.0],
                 [-3.0,-3.0,-3.0,-3.0,-3.0,-3.0,-3.0,-3.0,-3.0,-3.0],
                 [-4.0,-4.0,-4.0,-4.0,-4.0,-4.0,-4.0,-4.0,-4.0,-4.0],
                 [-5.0,-5.0,-5.0,-5.0,-5.0,-5.0,-5.0,-5.0,-5.0,-5.0],
                 [-6.0,-6.0,-6.0,-6.0,-6.0,-6.0,-6.0,-6.0,-6.0,-6.0],
                 [-7.0,-7.0,-7.0,-7.0,-7.0,-7.0,-7.0,-7.0,-7.0,-7.0]],
                 [[2.0, 1.0, 0.0,-1.0,-2.0,-3.0,-4.0,-5.0,-6.0,-7.0], # w dim
                 [2.0, 1.0, 0.0,-1.0,-2.0,-3.0,-4.0,-5.0,-6.0,-7.0],
                 [2.0, 1.0, 0.0,-1.0,-2.0,-3.0,-4.0,-5.0,-6.0,-7.0],
                 [2.0, 1.0, 0.0,-1.0,-2.0,-3.0,-4.0,-5.0,-6.0,-7.0],
                 [2.0, 1.0, 0.0,-1.0,-2.0,-3.0,-4.0,-5.0,-6.0,-7.0],
                 [2.0, 1.0, 0.0,-1.0,-2.0,-3.0,-4.0,-5.0,-6.0,-7.0],
                 [2.0, 1.0, 0.0,-1.0,-2.0,-3.0,-4.0,-5.0,-6.0,-7.0],
                 [2.0, 1.0, 0.0,-1.0,-2.0,-3.0,-4.0,-5.0,-6.0,-7.0],
                 [2.0, 1.0, 0.0,-1.0,-2.0,-3.0,-4.0,-5.0,-6.0,-7.0],
                 [2.0, 1.0, 0.0,-1.0,-2.0,-3.0,-4.0,-5.0,-6.0,-7.0]]
                ]),
                '1centrx5x4' : Image([[[ 2.0000,  2.0000,  2.0000,  2.0000,  2.0000,  2.0000,  2.0000, 2.0000],
         [ 1.5000,  1.5000,  1.5000,  1.5000,  1.5000,  1.5000,  1.5000,           1.5000],
         [ 0.5000,  0.5000,  0.5000,  0.5000,  0.5000,  0.5000,  0.5000,           0.5000],
         [-0.5000, -0.5000, -0.5000, -0.5000, -0.5000, -0.5000, -0.5000,          -0.5000],
         [-1.5000, -1.5000, -1.5000, -1.5000, -1.5000, -1.5000, -1.5000,          -1.5000],
         [-2.5000, -2.5000, -2.5000, -2.5000, -2.5000, -2.5000, -2.5000,          -2.5000],
         [-3.5000, -3.5000, -3.5000, -3.5000, -3.5000, -3.5000, -3.5000,          -3.5000],
         [-4.5000, -4.5000, -4.5000, -4.5000, -4.5000, -4.5000, -4.5000,          -4.5000],
         [-5.5000, -5.5000, -5.5000, -5.5000, -5.5000, -5.5000, -5.5000,          -5.5000],
         [-6.0000, -6.0000, -6.0000, -6.0000, -6.0000, -6.0000, -6.0000,          -6.0000]],

        [[ 2.5000,  1.8750,  0.6250, -0.6250, -1.8750, -3.1250, -4.3750,          -5.0000],
         [ 2.5000,  1.8750,  0.6250, -0.6250, -1.8750, -3.1250, -4.3750,          -5.0000],
         [ 2.5000,  1.8750,  0.6250, -0.6250, -1.8750, -3.1250, -4.3750,          -5.0000],
         [ 2.5000,  1.8750,  0.6250, -0.6250, -1.8750, -3.1250, -4.3750,          -5.0000],
         [ 2.5000,  1.8750,  0.6250, -0.6250, -1.8750, -3.1250, -4.3750,          -5.0000],
         [ 2.5000,  1.8750,  0.6250, -0.6250, -1.8750, -3.1250, -4.3750,          -5.0000],
         [ 2.5000,  1.8750,  0.6250, -0.6250, -1.8750, -3.1250, -4.3750,          -5.0000],
         [ 2.5000,  1.8750,  0.6250, -0.6250, -1.8750, -3.1250, -4.3750,          -5.0000],
         [ 2.5000,  1.8750,  0.6250, -0.6250, -1.8750, -3.1250, -4.3750,          -5.0000],
         [ 2.5000,  1.8750,  0.6250, -0.6250, -1.8750, -3.1250, -4.3750,          -5.0000]]]),
        }

    def test_fieldcreation(self):
        test_meta = {
            '1centrx5x5': ((1,5,5), [(1,1)]),
            '1centrx5x4': ((1,5,4), [(1,1)]),
            '2centrx5x5': ((2,5,5), [(1,1), (3,2)]),
            }
        for name, expected in self.raw_fields.items():
            with self.subTest(tensor=name):
                (N,H,W), centroids_list = test_meta[name]
                centroids = torch.tensor(centroids_list)
                assert expected.shape == (N,H,W,2), f"Input data wrongly configured, got {expected.shape}"
                actual = MMRPifPafTune._gen_field((N,H,W), centroids)
                torch.testing.assert_close(actual, expected.to(int), rtol=0, atol=0
                                           , msg=lambda msg: f"actual: {actual}\nexpected: {expected}\n\n{msg}\n\nFooter"
                                        )
    def test_fieldaggregation(self):
        """

        """
        input_tensors = self.raw_fields

        pass
    @unittest.skip("intermittend skipping")
    def test_resizing(self):
        """
        test that all resizing operations (image:TODO, bbox:TODO, mask:TODO, fields) are correct.
        """
        # take a 10x10 and downsize to 5x5 field
        #take a 10x8 and downsize to 5x4 field
        orig_pts = {
            '1centrx5x5': (KeyPoints([[2,2]],canvas_size=(10,10)), [(1,1)]),
            '1centrx5x4': (KeyPoints([[2,2]],canvas_size=(10,8)), [(1,1)]),
            '2centrx5x5': (KeyPoints([[2,2], [6,4]],canvas_size=(10,10)), [(1,1),(3,2)]),
        }

        #TODO: coverage for 5x4 case and 2centrx5x5 and upscaling scenarios


        to_test = [('1centrx5x5',(5,5)), ('1centrx5x4',(5,4)), ('2centrx5x5',(5,5))] # , ('1centrx5x4',(5,4))

        for sample, (H,W) in to_test:
            with self.subTest(modality='field', tensor=sample):
                if sample in self.large_fields.keys():

                    expected = Image(self.normed_fields[sample])
                    _input = self.large_fields[sample]
                    assert _input.shape[0] == 2 and expected.shape[0] == 2
                    transforms =  torchvision.transforms.v2.Resize(size=(H,W), interpolation=torchvision.transforms.v2.InterpolationMode.NEAREST) #NEAREST ist bugy but uses the lower index, NEAREST_Exact uses higher without the bugs
                    actual = transforms(_input)
                    torch.testing.assert_close(actual, expected, msg=lambda msg: f"actual: {actual}\nexpected: {expected}\n\n{msg}\n\nFooter")

            with self.subTest(modality='keypoint', tensor=sample):
                act_kypts = transforms(orig_pts[sample][0])
                expect_kypts = KeyPoints(orig_pts[sample][1],canvas_size=(H,W))
                torch.testing.assert_close(act_kypts, expect_kypts, msg=lambda msg: f"actual: {actual}\nexpected: {expected}\n\n{msg}\n\nFooter")


    def test_fieldnorming(self):
        """
         Norming by the image dims, div by dim*0.1
        """
        for name, input_tensor in self.aggregated_fields.items():
            with self.subTest(tensor=name):
                assert input_tensor.dim() == 3, f"Input data wrongly configured needs to be shape (H,W,2). Got {input_tensor.shape}"
                assert input_tensor.shape[2] == 2, f"Input data wrongly configured needs to be shape (H,W,2). Got {input_tensor.shape}"
                H, W, _ = input_tensor.shape
                step_unit = torch.tensor([H*0.1, W*0.1])
                actual = MMRPifPafTune.norm_fields(input_tensor, step_unit)
                expected = self.normed_fields[name]
                assert actual.shape == (2,H,W), f"Got {actual.shape}, expected {(2,H,W)}"
                torch.testing.assert_close(actual, expected, msg=lambda msg: f"actual: {actual}\nexpected: {expected}\n\n{msg}\n\nFooter")


    def test_keypoint_centroidcorrection(self):
        """
            upscale field, apply scale correction and move kypts to centroid
            kypts are 2 away from a centroid
        """
        img_dim = 10,8
        H,W = img_dim # , canvas_size=(H,W)
        input_keypoints = torch.tensor([[
                [0,0],
                [3,6], #[6,3],
                [3,9], #[9,3],
                [7,3]] #[3,7]]
            ])
        tested_points = 4
        expected_centroids = torch.tensor([
                [[2.,2.],[2.,2.], [2.,2.], [2.,2.]]
            ])
        input_centroids = torch.tensor([
                [1.,1.]
            ])
        #scaler = torch.tensor([[H*0.1], [W*0.1]])
        test_kpts = KeyPoints(input_keypoints, canvas_size=(H,W))
        field = self.large_fields['1centrx5x4']
        Y_pos = input_keypoints[0].T[1]
        X_pos = input_keypoints[0].T[0]
        assert field.shape == (2,10,8)
        kypts_field = field[None,:,Y_pos,X_pos]
        assert kypts_field.shape == (1,2,tested_points), f"Got {kypts_field.shape}"
        kypts_field = torch.movedim(kypts_field, 1,2)
        assert kypts_field.shape == (1,tested_points,2), f"Got {kypts_field.shape}"
        expected = torch.tensor([[[2.0,2.5],[-3.5,-0.625], [-6.,-0.625], [-0.5,-5.0]]])
        torch.testing.assert_close(kypts_field, expected, msg=lambda msg: f"actual: {kypts_field}\nexpected: {expected}\n\n{msg}\n\nFooter")
        scaler = torch.tensor([H*0.1, W*0.1])
        kypts_field = torch.mul(kypts_field, scaler)
        expected = torch.tensor([[[2.0,2.0],[-3.5,-0.5], [-6.0, -0.5],[-0.5,-4.0]]])
        assert kypts_field.shape == (1,tested_points,2), f"Got {kypts_field.shape}"
        torch.testing.assert_close(kypts_field, expected, msg=lambda msg: f"actual: {kypts_field}\nexpected: {expected}\n\n{msg}\n\nFooter")

        assert input_keypoints.shape == (1,tested_points,2), f"Got {input_keypoints.shape}"
        adjusted_kypts = KeyPoints(test_kpts + torch.flip(kypts_field, (2,)), canvas_size=(H,W)) # Shape (B,N,2)
        torch.testing.assert_close(adjusted_kypts, expected_centroids, rtol=0.1, atol=0.5, msg=lambda msg: f"actual: {adjusted_kypts}\nexpected: {expected_centroids}\n\n{msg}\n\nFooter")






if __name__ == '__main__':
    unittest.main()
