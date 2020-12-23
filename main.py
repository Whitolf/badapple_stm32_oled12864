import cv2.cv2 as cv
import serial
import time
import argparse

MSG_REQ_SYNC = 0xAA



def calc_checksum(data):
    checksum = 0
    for d in data:
        checksum ^= d
    return checksum


def msg_send_request(uart, id, payload):
    data = []
    data.append(MSG_REQ_SYNC)
    data.append(id)
    pd_len = len(payload)
    data.append(pd_len & 0xFF)
    data.append((pd_len >> 8) & 0xFF)
    data.append(calc_checksum(data))
    data.extend(payload)
    data=data[5:]
    uart.write(data)
    #print(data)
    #print("\n")
    uart.flush()



def img_to_stream(img):
    data = []
    for i in range(8):
        for j in range(128):
            tmp=[0 for m in range(8)]
            for m in range(8):
                tmp[m]=img[m+i*8][j]
            value = 0
            for pix in range(8):
                if tmp[pix] & 0x01:
                    value |= 1 << pix
            data.append(value)

    return data


def video_play(file, port, baudrate):
    fps = 30
    cap = cv.VideoCapture(file)

    print("cap is opend: {}".format(cap.isOpened()))
    vfps = cap.get(cv.CAP_PROP_FPS)
    print("FPS:{}".format(cap.get(cv.CAP_PROP_FPS)))
    uart = serial.Serial(port)
    uart.baudrate = baudrate
    data = []
    i = 0
    #print("\33[2J")
    #print("\033[0;0H")
    retry = False
    skip = vfps // fps
    if vfps % fps:
        skip += 4
    skip += 3
    delay = 1.0 / fps
    # print("skip = {}".format(skip))
    while True:

        if not retry:
            start_time = time.time()
            retval, img = cap.read()
            time.sleep(delay)
            i += 1
            if i % skip:
                continue
            cv.imshow(file, img)
            #img=cv.imread('./77.bmp')
            img = cv.cvtColor(img, cv.COLOR_RGB2GRAY)
            ret, img = cv.threshold(img, 0, 255, cv.THRESH_BINARY | cv.THRESH_OTSU)
            img = cv.resize(img, (128, 64))

            width = img.shape[0]
            height = img.shape[1]
            # print("\033[0;0H")
            # print("height={}, width={}".format(width, height))
            # print("")

            #cv.imshow(file, img)

            data = img_to_stream(img)

        msg_send_request(uart, i & 0xFF, data)
        try:
            retry = False
            cv.waitKey(1)
        except Exception:
            retry = True

        # time.sleep(delay)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Play video through oled')
    parser.add_argument('-f', '--file', help='The video file', default="./bad_apple.mp4")
    parser.add_argument('-p', '--port', help='The uart port', default="COM8")
    parser.add_argument('-b', '--baudrate', help='uart baudrate', default=1000000)
    args = parser.parse_args()
    video_play(args.file, args.port, args.baudrate)
