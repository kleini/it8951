
from PIL import Image, ImageChops

from .constants import DisplayModes

from .interface import EPD


class AutoDisplay:
    """
    This base class tracks changes to its frame_buf attribute, and automatically
    updates only the portions of the display that need to be updated

    Updates are done by calling the update() method, which derived classes should
    implement.
    """

    def __init__(self, width, height, flip=False, track_gray=False):
        self.width = width
        self.height = height
        self.flip = flip

        self.frame_buf = Image.new('L', (width, height), 0xFF)

        # keep track of what we have updated,
        # so that we can automatically do partial updates of only the
        # relevant portions of the display
        self.prev_frame = None

        self.track_gray = track_gray
        if track_gray:
            # keep track of what has changed since the last grayscale update
            # so that we make sure we clear any black/white intermediates
            # start out with no changes
            self.gray_change_bbox = None

    def _get_frame_buf(self):
        """
        Return the frame buf, rotated according to flip
        """
        if self.flip:
            return self.frame_buf.rotate(180)
        else:
            return self.frame_buf

    def draw_full(self, mode):
        """
        Write the full image to the device, and display it using mode
        """

        self.update(self._get_frame_buf().getdata(), (0, 0), (self.width, self.height), mode)

        if self.track_gray:
            if mode == DisplayModes.DU:
                diff_box = self._compute_diff_box(self.prev_frame, self._get_frame_buf(), round_to=4)
                self.gray_change_bbox = self._merge_bbox(self.gray_change_bbox, diff_box)
            else:
                self.gray_change_bbox = None

        self.prev_frame = self._get_frame_buf().copy()

    def clear(self):
        """
        Clear display, device image buffer, and frame buffer (e.g. at startup)
        """
        # set frame buffer to all white
        self.frame_buf.paste(0xFF, box=(0, 0, self.width, self.height))
        self.draw_full(DisplayModes.INIT)

    @classmethod
    def _compute_diff_box(cls, a, b, round_to=2):
        """
        Find the four coordinates giving the bounding box of differences between a and b
        making sure they are divisible by round_to

        Parameters
        ----------

        a : PIL.Image
            The first image

        b : PIL.Image
            The second image

        round_to : int
            The multiple to align the bbox to
        """
        box = ImageChops.difference(a, b).getbbox()
        if box is None:
            return None
        return cls._round_bbox(box, round_to)

    @staticmethod
    def _round_bbox(box, round_to=4):
        """
        Round a bounding box so the edges are divisible by round_to
        """
        minx, miny, maxx, maxy = box
        minx -= minx%round_to
        maxx += round_to-1 - (maxx-1)%round_to
        miny -= miny%round_to
        maxy += round_to-1 - (maxy-1)%round_to
        return (minx, miny, maxx, maxy)

    @staticmethod
    def _merge_bbox(a, b):
        """
        Return a bounding box that contains both bboxes a and b
        """
        if a is None:
            return b

        if b is None:
            return a

        minx = min(a[0], b[0])
        miny = min(a[1], b[1])
        maxx = max(a[2], b[2])
        maxy = max(a[3], b[3])
        return (minx, miny, maxx, maxy)

    def update(self, data, xy, dims, mode):
        raise NotImplementedError


class AutoEPDDisplay(AutoDisplay):
    """
    This class initializes the EPD, and uses it to display the updates
    """

    def __init__(self, epd=None, vcom=-2.06, **kwargs):

        if epd is None:
            epd = EPD(vcom=vcom)
        self.epd = epd
        AutoDisplay.__init__(self, self.epd.width, self.epd.height, **kwargs)

    def update(self, data, xy, dims, mode):

        # send image to controller
        self.epd.wait_display_ready()
        self.epd.load_img_area(
            data,
            xy=xy,
            dims=dims
        )

        # display sent image
#        self.epd.display_area(
#            xy,
#            dims,
#            mode
#        )
