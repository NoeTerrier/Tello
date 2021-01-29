# coding: utf8

import socket
import threading
import time
import cv2

COLOR_UI = (200, 200, 0)

def is_in_interval(x, center, size):
    return (center - size < x and x < center + size)

class Tello:
    def __init__(self, manual_connect = False):
        self.follow_face = False
        self.face_center = (0, 0)
        self.face_coords = None
        self.max_dist = 10
        self.face_cascade = cv2.CascadeClassifier('./haarcascade_frontalface_alt2.xml')

        self.ip = '192.168.10.1'
        self.isConnected = False
        self.alive = True
        self.threads = []

        self.command_port = 8889
        self.address = (self.ip, self.command_port)
        self.response = None
        self.overtime = 3

        self.state_port = 8890
        self.battery = 0
        self.barometer = 0

        self.video_frame = None  # NumPY array created by cv2 representing a frame from video stream
        self.video_port = 11111

        # init sockets

        self.command_socket = self.create_socket(self.command_port)
        self.state_socket = self.create_socket(self.state_port)

        self.create_thread(self.receive_response)
        self.create_thread(self.receive_state)

        if not manual_connect:
            self.init_connect()
            self.streamon()

        self.tello_video = cv2.VideoCapture('udp://@0.0.0.0:11111?overrun_nonfatal=1&fifo_size=50000000')  # create VideoCapture oject which represent Tello's camera
        # self.tello_video = cv2.VideoCapture(0);
        self.video_width = self.tello_video.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.video_heigth = self.tello_video.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.video_center = (int(self.video_width / 2), int(self.video_heigth / 2))
        self.create_thread(self.receive_video_data)


    """Create a thread for parallel processing tasks"""

    def create_thread(self, command):
        thread = threading.Thread(target=command)
        thread.daemon = True
        thread.start()
        self.threads.append(thread)
        return thread

    """Create a socket listening to a port"""

    def create_socket(self, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', port))
        sock.settimeout(self.overtime)
        return sock

    """Decorator which call a function in a loop and handle errors"""

    def loop_handle_errors(func):
        def loop(self):
            while self.alive:
                try:
                    func(self)
                except socket.timeout:
                    pass
                except Exception as err:
                    print(err)

        return loop

    """Receive Command response of the drone from port 8889"""

    @loop_handle_errors
    def receive_response(self):
        self.response, ip = self.command_socket.recvfrom(1024)
        if self.response:
            print(str(self.response))

    """Receive state of the drone from port 8890"""

    @loop_handle_errors
    def receive_state(self):
        response, ip = self.state_socket.recvfrom(1024)
        if response:
            response_table = str(response)[2:-7].split(';')
            data_dico = {}
            for pair in response_table:
                set = pair.split(':')
                data_dico[set[0]] = set[1]
            self.battery = data_dico['bat']
            self.barometer = data_dico['baro']

    """Receive video frame of the drone from port 11111"""

    @loop_handle_errors
    def receive_video_data(self):
        ret, frame = self.tello_video.read()  # read() method return true, image if an image has been grabbed, else false
        if ret:
            self.detect_face(frame)
            cv2.circle(frame, self.video_center, 10, COLOR_UI, 2)
            self.video_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # transform the frame from BGR to RGB

    """Detect faces in a video frame"""

    def detect_face(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        face = self.face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=4)
        if len(face) > 0:
            for x, y, w, h in face:
                cv2.rectangle(frame, (x, y), (x+w, y+h), COLOR_UI, 2)
                cv2.rectangle(frame, (x-1, y-20), (x+70, y), COLOR_UI, cv2.FILLED)
                cv2.putText(frame, "Face", (x, y), cv2.FONT_HERSHEY_PLAIN, 1.5, (255,255,255), 1)
                self.face_center = (int(x + w / 2), int(y + h / 2))
                cv2.line(frame, (self.face_center[0], self.face_center[1]-10),
                                (self.face_center[0], self.face_center[1]+10),
                                COLOR_UI, 2)
                cv2.line(frame, (self.face_center[0]-10, self.face_center[1]),
                                (self.face_center[0]+10, self.face_center[1]),
                                COLOR_UI, 2)
                self.face_coords = (x, y, w, h)
        else:
            self.face_coords = None

    """Return the current frame"""

    def get_frame(self):
        return self.video_data

    def align_with_face(self):
        if not self.follow_face:
            self.face_align_thread = self.create_thread(self.align_axes)
            self.follow_face = True
            print("Align with face")

    def stop_align(self):
        self.follow_face = False
        self.face_align_thread.join()
        self.threads.remove(self.face_align_thread)
        print("Stop alignment")

    def align_axes(self):
        while self.alive and self.follow_face:
            if not is_in_interval(self.face_center[0], self.video_center[0], self.max_dist):
                self.turn_left() if self.video_center[0] - self.max_dist > self.face_center[0] else self.turn_right()
                time.sleep(1)
            if not is_in_interval(self.face_center[1], self.video_center[1], self.max_dist):
                self.up() if self.video_center[1] - self.max_dist > self.face_center[1] else self.down()
                time.sleep(1)

    def send_command(self, command):
        self.command_socket.sendto(command.encode('utf-8'), self.address)
        print('sent : ' + command)

    # control command:
    def connect(self):
        self.send_command('command')

    def init_connect(self):
        self.connect()
        last_send = time.time()
        while self.response != b'ok':
            if time.time() - last_send >= self.overtime:
                self.connect()
                last_send = time.time()
        else:
            self.isConnected = True
            print("Tello connected")

    def streamon(self):
        self.send_command('streamon')

    def takeoff(self):
        self.send_command('takeoff')

    def land(self):
        self.send_command('land')

    def turn_right(self):
        self.send_command('cw 30')

    def turn_left(self):
        self.send_command('ccw 30')

    def up(self):
        self.send_command('up 30')

    def down(self):
        self.send_command('down 30')

    def forward(self):
        self.send_command('forward 30')

    def back(self):
        self.send_command('back 30')

    def left(self):
        self.send_command('left 30')

    def right(self):
        self.send_command('right 30')

    def disconect(self):
        self.alive = False

        for thread in self.threads:
            thread.join()
            print(str(thread) + " joined successfully")

        self.command_socket.close()
        print(str(self.command_socket) + " closed successfully")
        self.state_socket.close()
        print(str(self.state_socket) + " closed successfully")

        self.tello_video.release()
        print("Video released successfully")

        print("Tello disconected")


if __name__ == '__main__':
    drone = Tello()
