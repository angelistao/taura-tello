from djitellopy import Tello 
import cv2

tello = Tello()

tello.connect()
tello.stream_on()

tello_video = cv2.VideoCapture(str(tello.get_udp_video_address()))

while True:
    try:
        ret, frame = tello_video.read()
        if ret:
            cv2.imshow(frame)
            cv2.waitKey(1)

    except Exception as err:
        tello_video.release()
        cv2.destroyAllWindows()
        tello.streamoff()
        print(err)

