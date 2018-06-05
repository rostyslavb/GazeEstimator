from app.device import SceneObj
from numpy import cross
from numpy import array
from numpy.linalg import norm
from app.parser import quaternion_to_angle_axis, face_point_to_array
from numpy import sum, abs, sqrt
from scipy.optimize import minimize

class Actor(SceneObj):


    def __init__(self, name, origin):
        super().__init__(name=name, origin=origin)
        self.eyeball_radius = 0.012
        self.landmarks3D = {
            'eyes': {
                'left': {
                    'rectangle': None,
                    'center': None,
                    'gaze': None
                },
                'right': {
                    'rectangle': None,
                    'center': None,
                    'gaze': None
                }
            },
            'nose': None,
            'chin': None
        }

    def to_learning_dataset(self, img_left_name, img_rigth_name, camera):
        return {
            'eyes': {
                'left': {
                    'gaze_norm': camera.vectors_to_self(
                        self.landmarks3D['eyes']['left']['gaze']/norm(self.landmarks3D['eyes']['left']['gaze'])).tolist(),
                    'image': img_left_name,
                    'center': camera.vectors_to_self(self.landmarks3D['eyes']['left']['center']).tolist()
                },
                'right': {
                    'gaze_norm': camera.vectors_to_self(
                        self.landmarks3D['eyes']['right']['gaze']/norm(self.landmarks3D['eyes']['right']['gaze'])).tolist(),
                    'image': img_rigth_name,
                    'center': camera.vectors_to_self(self.landmarks3D['eyes']['right']['center']).tolist()
                }
            },
            'rotation_norm': camera.vectors_to_self(self.get_norm_vector_to_face()/norm(self.get_norm_vector_to_face())).tolist()
        }

    def set_landmarks3d(self, face_points):
        face_points = array(face_points)
        right_eye_center = [843, 1097, 1095, 1096, 1091, 1090, 1092, 1099, 1094, 1065, 1100, 1101, 1102, 992, 846, 777,
                            776, 728, 731, 873, 733, 876, 749, 752, 992]

        left_eye_center = [210, 1111, 1109, 1108, 1103, 1104, 1105, 1112, 1106, 1107, 1113, 1114, 1115, 1116, 188, 211,
                           137, 238, 244, 241, 121, 153, 187, 316]

        # Function for OLS
        def objective_function(center, eye):
            return sum(abs(norm(center - face_points[eye, :], axis=1) - self.eyeball_radius))

        self.landmarks3D['eyes']['left']['rectangle'] = array([face_points[i] for i in [1080, 201, 289, 151]])
        self.landmarks3D['eyes']['right']['rectangle'] = array([face_points[i] for i in [1084, 847, 947, 772]])
        self.landmarks3D['eyes']['left']['center'] = minimize(lambda x: objective_function(x, left_eye_center),
                                                               x0=face_points[left_eye_center[0]]).x
        self.landmarks3D['eyes']['right']['center'] = minimize(lambda x: objective_function(x, right_eye_center),
                                                               x0=face_points[right_eye_center[0]]).x
        self.landmarks3D['nose'] = array(face_points[18])
        self.landmarks3D['chin'] = array(face_points[4])
        return self

    def set_landmarks3d_eye_rectangles(self, left_eye_rect, right_eye_rect):
        self.landmarks3D['eyes']['left']['rectangle'] = left_eye_rect
        self.landmarks3D['eyes']['right']['rectangle'] = right_eye_rect
        return self

    def set_landmarks3d_eye_centers(self, left_eye_center, right_eye_center):
        self.landmarks3D['eyes']['left']['center'] = left_eye_center
        self.landmarks3D['eyes']['right']['center'] = right_eye_center
        return self

    def set_landmarks3d_nose_chin(self, nose, chin):
        self.landmarks3D['nose'] = nose
        self.landmarks3D['chin'] = chin
        return self

    def set_landmarks3d_gazes(self, x, y, screen):
        gaze_point_origin_space = screen.point_to_origin(x, y).reshape(3)
        self.landmarks3D['eyes']['left']['gaze'] = gaze_point_origin_space - self.landmarks3D['eyes']['left']['center']
        self.landmarks3D['eyes']['right']['gaze'] = gaze_point_origin_space - self.landmarks3D['eyes']['right']['center']


    # def set_landmarks2d(self, shape_from_dlib):
    #     self.landmarks2D = shape_from_dlib
    #     return self
    #
    # def get_eye_landmarks2d(self):
    #     return self.landmarks2D[[37, 40] + [43, 46]].reshape(2, -1, 2)

    # def get_eye_rectangle_coordinates(self, out_shape):
    #     return self.get_eye_landmarks2d().mean(axis=1, dtype=int) - out_shape[::-1].reshape(1, 2) // 2

    def set_rotation(self, face_rotation_quaternion):
        self.rotation = quaternion_to_angle_axis(face_rotation_quaternion)
        return self

    def set_translation(self, key='nose'):
        self.translation = self.landmarks3D[key]
        return self

    def get_norm_vector_to_face(self):
        return cross(self.landmarks3D['chin'] - self.landmarks3D['eyes']['left']['center'],
                     self.landmarks3D['chin'] - self.landmarks3D['eyes']['right']['center'])
