from socket import *
import sys
import os
import time
import struct
import hashlib

def handle_duplicates(packets):
  i = 0
  while i < len(packets) - 1:
    if packets[i][0] == packets[i+1][0]:
      del packets[i+1]
    else:
      i += 1
  return packets

def extract(packet):
  num, = struct.unpack("!I", packet[0:4])
  hashdata = packet[4:20]
  return num, hashdata, packet[20:]

def write_file(recvfile,packets):
  with open(recvfile, 'wb') as f:
    #print('File opened')
    for p in packets:
      data = p[1]
      f.write(data)    
  f.close() 

def recv_file(s,host,port):
  begin = time.time()
  timeout = 2
  ack = 0
  packets = []

  while True:
    # wait if you have no data
    if time.time() - begin > timeout:
      break  

    try:  
      packet = s.recv(1105)
      if packet:
        num, hashdata, data = extract(packet)
        datahash = hashlib.md5(data).digest()

        # Send acknlowedgement to the sender
        if num == ack and datahash == hashdata:
          s.sendto(str(ack).encode(),(host,port))
          ack = ack + 1
          packets.append((num, data))
        else:
          s.sendto(str(ack-1).encode(),(host,port))
        begin = time.time()
      else:
        time.sleep(0.01)
    except error:
      pass  

  return packets   

def main(argv):
  host = argv[0]
  port = int(argv[1])
  filename = argv[2]
  recvfile = argv[3]

  s = socket(AF_INET, SOCK_DGRAM)
  s.setblocking(0)

  # send filename
  s.sendto(filename.encode(),(host,port))

  # recv file
  packets = recv_file(s,host,port)
      
  # handle reorder
  sorted(packets, key=lambda x: x[0])

  # handle duplicates
  packets = handle_duplicates(packets)

  # write file
  write_file(recvfile,packets)

  # close socket
  s.close()

if __name__ == '__main__':
  main(sys.argv[1:])