"""Test closing contour detection."""
import gio

def test_closure_detection():
    g = 100 * gio.generate_random_surface(200, res=3, octaves=3, random_seed=99999999)
    contours = gio.find_closures(g.data, min_area=100, min_height=10)
    assert len(contours) == 9
    assert contours[7].area - 4274.59701221374 < 1e-9
    # I can't figure out how to get the level from Polygon
    # assert contours[7].z == 29
