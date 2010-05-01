import numpy as np

from nipy.modalities.fmri.api import FmriImageList
from nipy.modalities.fmri.pca import pca_image
from nipy.core.api import Image
from nipy.core.image.xyz_image import XYZImage
from nipy.core.image.image import rollaxis as image_rollaxis
from nipy.io.api import  load_image
from nipy.testing import *

data_dict = {}

def setup():
    tmp_img = load_image(funcfile)
    
    # For now, img is an Image
    # instead of an XYZImage

    A = np.identity(4)
    A[:3,:3] = tmp_img.affine[:3,:3]
    A[:3,-1] = tmp_img.affine[:3,-1]
    
    xyz_data = tmp_img.get_data()
    xyz_img = XYZImage(xyz_data, A,
                       tmp_img.axes.coord_names[:3] + ('t',))
    
    # If load_image returns an XYZImage, I'd really be
    # starting from xyz_img, so from here

    # Here, I'm just doing this so I know that
    # img.shape[0] is the number of volumes

    img = image_rollaxis(Image(xyz_img._data, xyz_img.coordmap), 't')
    data_dict['nimages'] = img.shape[0]

    # It might be worth to make
    # data a public attribute of Image/XYZImage
    # and we might rename get_data-> data_as_array = np.asarray(self.data)
    # Then, the above would not access a private attribute
    
    # Below, I am just making a mask
    # because I already have img, I 
    # know I can do this
    # In principle, though, the pca function
    # will just take another XYZImage as a mask

    img_data = img.get_data()
    first_frame = img_data[0]

    mask = XYZImage(np.greater(np.asarray(first_frame), 500).astype(np.float64), A, xyz_img.axes.coord_names[:3])

    data_dict['fmridata'] = xyz_img
    data_dict['mask'] = mask
    data_dict['img'] = img

    print data_dict['mask'].shape, np.sum(np.array(data_dict['mask']))


def test_PCAMask():
    nimages = data_dict['nimages']

    ntotal = nimages - 1
    ncomp = 5
    p = pca_image(data_dict['fmridata'], data_dict['mask'], ncomp=ncomp)

    yield assert_equal, p['rank'], ntotal
    yield assert_equal, p['components over t'].shape, (ncomp,
                                                         nimages)
    yield assert_equal, p['images'].shape, data_dict['mask'].shape + (ncomp,)
    yield assert_equal, p['pcnt_var'].shape, (ntotal,)
    yield assert_almost_equal, p['pcnt_var'].sum(), 100.

    yield assert_equal, p['images'].axes.coord_names, ['i','j','k','PCA components']
    yield assert_equal, p['images'].xyz_transform, data_dict['mask'].xyz_transform

def test_not_spatial():
    # we can't do PCA over spatial axes
    ncomp = 5
    for i, o, n in zip('ijk', 'xyz', [0,1,2]):
        yield assert_raises, ValueError, pca_image, data_dict['fmridata'], data_dict['mask'], ncomp, i
        yield assert_raises, ValueError, pca_image, data_dict['fmridata'], data_dict['mask'], ncomp, o
        yield assert_raises, ValueError, pca_image, data_dict['fmridata'], data_dict['mask'], ncomp, n


def test_PCAMask_nostandardize():
    nimages = data_dict['nimages']

    ntotal = nimages - 1
    ncomp = 5
    p = pca_image(data_dict['fmridata'], data_dict['mask'], ncomp=ncomp, standardize=False)

    yield assert_equal, p['rank'], ntotal
    yield assert_equal, p['components over t'].shape, (ncomp,
                                                         nimages)
    yield assert_equal, p['images'].shape, data_dict['mask'].shape + (ncomp,)
    yield assert_equal, p['pcnt_var'].shape, (ntotal,)
    yield assert_almost_equal, p['pcnt_var'].sum(), 100.

    yield assert_equal, p['images'].axes.coord_names, ['i','j','k','PCA components']
    yield assert_equal, p['images'].xyz_transform, data_dict['mask'].xyz_transform

def test_PCANoMask():
    nimages = data_dict['nimages']
    ntotal = nimages - 1
    ncomp = 5
    p = pca_image(data_dict['fmridata'], ncomp=ncomp)

    yield assert_equal, p['rank'], ntotal
    yield assert_equal, p['components over t'].shape, (ncomp,
                                                         nimages)
    yield assert_equal, p['images'].shape, data_dict['mask'].shape + (ncomp,)
    yield assert_equal, p['pcnt_var'].shape, (ntotal,)
    yield assert_almost_equal, p['pcnt_var'].sum(), 100.

    yield assert_equal, p['images'].axes.coord_names, ['i','j','k','PCA components']
    yield assert_equal, p['images'].xyz_transform, data_dict['mask'].xyz_transform

def test_PCANoMask_nostandardize():
    nimages = data_dict['nimages']
    ntotal = nimages - 1
    ncomp = 5
    p = pca_image(data_dict['fmridata'], ncomp=ncomp, standardize=False)

    yield assert_equal, p['rank'], ntotal
    yield assert_equal, p['components over t'].shape, (ncomp,
                                                         nimages)
    yield assert_equal, p['images'].shape, data_dict['mask'].shape + (ncomp,)
    yield assert_equal, p['pcnt_var'].shape, (ntotal,)
    yield assert_almost_equal, p['pcnt_var'].sum(), 100.

    yield assert_equal, p['images'].axes.coord_names, ['i','j','k','PCA components']
    yield assert_equal, p['images'].xyz_transform, data_dict['mask'].xyz_transform

def test_keep():
    """
    Data is projected onto k=10 dimensional subspace
    then has its mean removed.
    Should still have rank 10.

    """
    k = 10
    ncomp = 5
    nimages = data_dict['nimages']
    ntotal = k
    X = np.random.standard_normal((nimages, k))
    p = pca_image(data_dict['fmridata'], ncomp=ncomp, design_keep=X)

    yield assert_equal, p['rank'], ntotal
    yield assert_equal, p['components over t'].shape, (ncomp,
                                                         nimages)
    yield assert_equal, p['images'].shape, data_dict['mask'].shape + (ncomp,)
    yield assert_equal, p['pcnt_var'].shape, (ntotal,)
    yield assert_almost_equal, p['pcnt_var'].sum(), 100.

    yield assert_equal, p['images'].axes.coord_names, ['i','j','k','PCA components']
    yield assert_equal, p['images'].xyz_transform, data_dict['mask'].xyz_transform

def test_resid():
    """
    Data is projected onto k=10 dimensional subspace
    then has its mean removed.
    Should still have rank 10.

    """
    k = 10
    ncomp = 5
    nimages = data_dict['nimages']
    ntotal = k
    X = np.random.standard_normal((nimages, k))
    p = pca_image(data_dict['fmridata'], ncomp=ncomp, design_resid=X)

    yield assert_equal, p['rank'], ntotal
    yield assert_equal, p['components over t'].shape, (ncomp,
                                                         nimages)
    yield assert_equal, p['images'].shape, data_dict['mask'].shape + (ncomp,)
    yield assert_equal, p['pcnt_var'].shape, (ntotal,)
    yield assert_almost_equal, p['pcnt_var'].sum(), 100.

    yield assert_equal, p['images'].axes.coord_names, ['i','j','k','PCA components']
    yield assert_equal, p['images'].xyz_transform, data_dict['mask'].xyz_transform




def test_both():
    k1 = 10
    k2 = 8
    ncomp = 5
    nimages = data_dict['nimages']
    ntotal = k1
    X1 = np.random.standard_normal((nimages, k1))
    X2 = np.random.standard_normal((nimages, k2))
    p = pca_image(data_dict['fmridata'], ncomp=ncomp, design_resid=X2, design_keep=X1)

    yield assert_equal, p['rank'], ntotal
    yield assert_equal, p['components over t'].shape, (ncomp,
                                                         nimages)
    yield assert_equal, p['images'].shape, data_dict['mask'].shape + (ncomp,)
    yield assert_equal, p['pcnt_var'].shape, (ntotal,)
    yield assert_almost_equal, p['pcnt_var'].sum(), 100.

    yield assert_equal, p['images'].axes.coord_names, ['i','j','k','PCA components']
    yield assert_equal, p['images'].xyz_transform, data_dict['mask'].xyz_transform


def test_5d():
    # What happend to a 5d image, 
    # we should get 4d images back

    xyz_img = data_dict['fmridata']
    xyz_data = xyz_img.get_data()
    affine = xyz_img.affine

    xyz_data_5d = xyz_data.reshape(xyz_data.shape + (1,))
    fived = XYZImage(xyz_data_5d, affine, 'ijktv')

    mask_data = data_dict['mask'].get_data()
    mask_data = mask_data.reshape(mask_data.shape + (1,))
    mask4d = XYZImage(mask_data, affine, 'ijkv')

    nimages = data_dict['nimages']

    ntotal = nimages - 1
    ncomp = 5
    p = pca_image(fived, mask4d, ncomp=ncomp)

    yield assert_equal, p['rank'], ntotal
    yield assert_equal, p['components over t'].shape, (ncomp,
                                                         nimages)
    yield assert_equal, p['images'].shape, xyz_data.shape[:3] + (ncomp, 1)
    yield assert_equal, p['pcnt_var'].shape, (ntotal,)
    yield assert_almost_equal, p['pcnt_var'].sum(), 100.

    yield assert_equal, p['images'].axes.coord_names, ['i','j','k','PCA components','v']
    yield assert_equal, p['images'].xyz_transform, xyz_img.xyz_transform

    xyz_data_5d = xyz_data.reshape(xyz_data.shape[:3] + (1,xyz_data.shape[3]))
    fived = XYZImage(xyz_data_5d, affine, list('ijkv') + ['group'])

    mask_data = data_dict['mask'].get_data()
    mask_data = mask_data.reshape(mask_data.shape + (1,))
    mask4d = XYZImage(mask_data, affine, 'ijkv')

    nimages = data_dict['nimages']

    ntotal = nimages - 1
    ncomp = 5
    # the axis does not have to be time
    p = pca_image(fived, mask4d, ncomp=ncomp, axis='group')

    yield assert_equal, p['components over group'].shape, (ncomp,
                                                         nimages)
    yield assert_equal, p['images'].axes.coord_names, ['i','j','k','v','PCA components']
    yield assert_equal, p['images'].shape, xyz_data.shape[:3] + (1, ncomp)