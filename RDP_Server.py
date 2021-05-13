from socket import *
import sys
import os
import time
import struct
import hashlib

def make_packet(acknum, md5_value, data='b'):
  #ackbytes = (acknum).to_bytes(4, byteorder='little', signed=True)
  ackbytes = struct.pack("!I",acknum)
  return ackbytes + md5_value + data

def file_exists(filename):
  return os.path.isfile(filename)

def make_packets(filename):
  # Open file
  if file_exists(filename):
    print('File exist.'+filename)
    f = open(filename,'rb')
  else:
    print('File does not exist.')
  
  packets = []
  contents = f.read(1020)
  num = 0
  while True:
    if contents == '':
      break
    md5_value = hashlib.md5(contents).digest()
    packets.append(make_packet(num, md5_value, contents))
    num += 1
    contents = f.read(1020)
  f.close()
  return packets

def time_out(start_time):
  if start_time != -1:
    return False
  return time.time() - start_time >= 0.5

def send_packets(packets,addr,s):
  nums = len(packets)
  window = 5 if nums < 5 else nums
  base = 0
  next_frame = 0
  while base < nums:
    # Send all packets within the window
    while next_frame < base + window and next_frame < nums:
      #print('Sending packet ', next_frame)
      s.sendto(packets[next_frame], addr)
      next_frame += 1

    # Wait till time is up or acknowledgement
    start_time = time.time()
    while (start_time != -1) and not time_out(start_time):
      try:
        data = s.recvfrom(1024)
      except error:
        continue

      if data:
        ack = data[0].decode()
        #print('Got acknowledgement ', ack)
        if int(ack) >= base:
          base = int(ack) + 1
          start_time = -1
        else:
          base = int(ack)
          next_frame = base
          start_time = -1

    if time_out(start_time):
      start_time = -1
      next_frame = base
    else:
      print('Shifting window.')
      window = nums if nums < base else base


def main(argv):
  host = argv[0]
  port = int(argv[1])
  s = socket(AF_INET, SOCK_DGRAM)
  s.setblocking(0)
  s.bind((host,port))
  print('Listening on: ' + host + ':' + str(port))

  while True:

    # recive filename
    try:
      recdata, addr = s.recvfrom(1024)
    except error:
      continue
    filename = recdata.decode()

    # open file, make packets
    packets = make_packets(filename)

    # send packets
    send_packets(packets,addr,s)

    time.sleep(2)
    print('Listening on: ' + host + ':' + str(port))

if __name__ == '__main__':
  main(sys.argv[1:])