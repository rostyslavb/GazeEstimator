from numpy import array
from numpy.linalg import inv

from cv2 import circle
from cv2 import line
from cv2 import putText

from cv2 import cvtColor
from cv2 import equalizeHist

from cv2 import projectPoints
from cv2 import findHomography
from cv2 import warpPerspective

from cv2 import COLOR_RGB2GRAY
from cv2 import FONT_HERSHEY_SIMPLEX

from app.specularity_removal import remove_specularity as rm_specularity


class Frame:

    def __init__(self, camera, image):
        self.camera = camera
        self.image = image.astype('uint8')

    @staticmethod
    def draw_points(image, points, colors=None, radius=4, default_color=(255, 0, 0)):
        if colors is None:
            colors = [default_color] * len(points)
        for point, color in zip(points, colors):
            circle(image, tuple(point.astype(int)), radius, color, -1)

    @staticmethod
    def draw_labels(image, labels, positions, colors=(None,), size=4, default_color=(255, 255, 255)):
        for label, position, color in zip(labels, positions, colors):
            if color is None:
                color = default_color
            putText(image, label, tuple((position+14).astype(int)), FONT_HERSHEY_SIMPLEX, size, color, 4, lineType=3)

    @staticmethod
    def draw_lines(image, start_points, end_points, default_color=(255, 0, 0), thickness=2):
        for start, end in zip(start_points, end_points):
            line(image, tuple(start), tuple(end), default_color, thickness, lineType=2)

    def get_projected_coordinates(self, vectors):
        return projectPoints(vectors,
                             -self.camera.rotation,
                             -(inv(self.camera.get_rotation_matrix()) @ self.camera.translation),
                             self.camera.matrix,
                             self.camera.distortion)[0].reshape(-1, 2)

    def project_vectors(self, vectors, **kwargs):
        self.draw_points(self.image, self.get_projected_coordinates(vectors.reshape((-1, 3))).astype(int), **kwargs)
        return self

    def project_lines(self, start_points, end_points, **kwargs):
        self.draw_lines(self.image,
                        self.get_projected_coordinates(start_points.reshape((-1, 3))).astype(int),
                        self.get_projected_coordinates(end_points.reshape((-1, 3))).astype(int),
                        **kwargs)
        return self

    def extract_rectangle(self, coord, shape):
        """

        :param coord: Left-upper corner.
        :param shape: Tuple (height, width)
        :return:
        """
        return self.image[coord[0]:coord[0]+shape[0], coord[1]:coord[1]+shape[1]]

    def extract_eyes_from_person(self, person, resolution=(60, 36), equalize_hist=False, to_grayscale=False, remove_specularity=False):
        # eye planes
        left_norm_image_plane = array([[resolution[0], 0.0          ],
                                        [0.0,           0.0          ],
                                        [0.,            resolution[1]],
                                        [resolution[0], resolution[1]]])
        right_norm_image_plane = array([[0.0,          0.0          ],
                                         [resolution[0], 0.0         ],
                                         [resolution[0], resolution[1]],
                                         [0.,            resolution[1]]])

        left_eye_projection = self.get_projected_coordinates(person.get_eye_rectangle('left'))
        right_eye_projection = self.get_projected_coordinates(person.get_eye_rectangle('right'))

        homography, status = findHomography(left_eye_projection, left_norm_image_plane)
        left_eye_frame = warpPerspective(self.image, homography, resolution)

        homography, status = findHomography(right_eye_projection, right_norm_image_plane)
        right_eye_frame = warpPerspective(self.image, homography, resolution)

        if to_grayscale:
            left_eye_frame, right_eye_frame = cvtColor(left_eye_frame, COLOR_RGB2GRAY), \
                                              cvtColor(right_eye_frame, COLOR_RGB2GRAY)
        if equalize_hist:
            left_eye_frame, right_eye_frame = equalizeHist(left_eye_frame), equalizeHist(right_eye_frame)

        if remove_specularity:
            left_eye_frame, right_eye_frame = rm_specularity(left_eye_frame), rm_specularity(right_eye_frame)

        return left_eye_frame, right_eye_frame
