#!/usr/bin/python

import sys
import os
import glob
import zlib
import struct
#import base64

MAGIC_NO_COMPRESS_START = 0x03
MAGIC_COMPRESS_START = 0x04
MAGIC_COMPRESS_START1 = 0x05

MAGIC_END = 0x00

IO_BUFFER_SIZE = 4096

# This variable defines how deep you want the tool to
# scan subfolders to find clog files
recursive_level = 5
lastseq = 0


def IsGoodLogBuffer(_buffer, _offset, count):
    if _offset == len(_buffer): return (True, '')

    if MAGIC_NO_COMPRESS_START == _buffer[
            _offset] or MAGIC_COMPRESS_START == _buffer[
                _offset] or MAGIC_COMPRESS_START1 == _buffer[_offset]:
        headerLen = 1 + 2 + 1 + 1 + 4 + 4
    else:
        return (False, '_buffer[%d]:%d != MAGIC_NUM_START' %
                (_offset, _buffer[_offset]))

    if _offset + headerLen + 1 + 1 > len(_buffer):
        return (False, 'offset:%d > len(buffer):%d' % (_offset, len(_buffer)))
    #length = struct.unpack_from("I", buffer(_buffer, _offset+headerLen-4-4, 4))[0]
    length = struct.unpack_from(
        "I",
        memoryview(_buffer)[_offset + headerLen - 4 - 4:_offset + headerLen -
                            4])[0]

    if _offset + headerLen + length + 1 > len(_buffer):
        return (False, 'log length:%d, end pos %d > len(buffer):%d' %
                (length, _offset + headerLen + length + 1, len(_buffer)))
    if MAGIC_END != _buffer[_offset + headerLen + length]:
        return (False, 'log length:%d, buffer[%d]:%d != MAGIC_END' %
                (length, _offset + headerLen + length,
                 _buffer[_offset + headerLen + length]))

    if (1 >= count): return (True, '')
    else:
        return IsGoodLogBuffer(_buffer, _offset + headerLen + length + 1,
                               count - 1)


def GetLogStartPos(_buffer, _count):
    offset = 0
    while True:
        if offset >= int(len(_buffer)): break

        if MAGIC_NO_COMPRESS_START == _buffer[
                offset] or MAGIC_COMPRESS_START == _buffer[
                    offset] or MAGIC_COMPRESS_START1 == _buffer[offset]:
            if IsGoodLogBuffer(_buffer, offset, _count)[0]: return offset
        offset += 1

    return -1


def DecodeBuffer(_buffer, _offset, _outbuffer):
    if _offset >= int(len(_buffer)): return -1
    # if _offset + 1 + 4 + 1 + 1 > len(_buffer): return -1
    ret = IsGoodLogBuffer(_buffer, int(_offset), 1)
    if not ret[0]:
        fixpos = int(GetLogStartPos(_buffer[int(_offset):], 1))
        if -1 == int(fixpos):
            return -1
        else:
            _outbuffer.extend(
                "[F]decode_log_file.py decode error len=%d, result:%s \n" %
                (fixpos, ret[1]))
            _offset += fixpos

    if MAGIC_NO_COMPRESS_START == _buffer[
            _offset] or MAGIC_COMPRESS_START == _buffer[
                _offset] or MAGIC_COMPRESS_START1 == _buffer[_offset]:
        headerLen = 1 + 2 + 1 + 1 + 4 + 4
    else:
        _outbuffer.extend("in DecodeBuffer _buffer[%d]:%d != MAGIC_NUM_START" %
                          (_offset, _buffer[_offset]))
        return -1

    length = struct.unpack_from(
        "I",
        memoryview(_buffer)[_offset + headerLen - 4 - 4:_offset + headerLen -
                            4])[0]
    #length = struct.unpack_from("I", buffer(_buffer, _offset+headerLen-4-4, 4))[0]

    tmpbuffer = bytearray(length)

    seq = struct.unpack_from(
        "H",
        memoryview(_buffer)[_offset + headerLen - 4 - 4 - 2 - 2:_offset +
                            headerLen - 4 - 4 - 2])[0]
    #seq=struct.unpack_from("H", buffer(_buffer, _offset+headerLen-4-4-2-2, 2))[0]
    begin_hour = struct.unpack_from(
        "c",
        memoryview(_buffer)[_offset + headerLen - 4 - 4 - 1 - 1:_offset +
                            headerLen - 4 - 4 - 1])[0]
    #begin_hour=struct.unpack_from("c", buffer(_buffer, _offset+headerLen-4-4-1-1, 1))[0]
    end_hour = struct.unpack_from(
        "c",
        memoryview(_buffer)[_offset + headerLen - 4 - 4 - 1:_offset +
                            headerLen - 4 - 4])[0]
    #end_hour=struct.unpack_from("c", buffer(_buffer, _offset+headerLen-4-4-1, 1))[0]

    global lastseq
    if int(seq) != 0 and int(seq) != 1 and int(lastseq) != 0 and int(seq) != (int(lastseq) + 1):
        print("--------")
       # _outbuffer.extend("[F]decode_log_file.py log seq:%d-%d is missing\n" %
                          #(int(lastseq) + 1, int(seq) - 1))
        
    if int(seq) != 0:
        lastseq = int(seq)

    tmpbuffer[:] = _buffer[int(_offset) + int(headerLen):int(_offset) + int(headerLen) + int(length)]

    try:
        decompressor = zlib.decompressobj(-zlib.MAX_WBITS)

        if MAGIC_COMPRESS_START == _buffer[_offset]:
            tmpbuffer = decompressor.decompress(str(tmpbuffer))
            print("MAGIC_COMPRESS_START")
        elif MAGIC_COMPRESS_START1 == _buffer[int(_offset)]:
            decompressor = zlib.decompressobj(-zlib.MAX_WBITS)
            decompress_data = bytearray()
            while len(tmpbuffer) > 0:
                single_log_len = struct.unpack_from(
                    "H",
                    memoryview(tmpbuffer)[0:2])[0]
                #single_log_len = struct.unpack_from("H", buffer(tmpbuffer, 0, 2))[0]
                #decompress_data.extend(base64.decodestring(tmpbuffer[2:single_log_len+2]))
                decompress_data.extend(tmpbuffer[2:single_log_len + 2])
                tmpbuffer[:] = tmpbuffer[single_log_len + 2:len(tmpbuffer)]

            tmpbuffer = decompressor.decompress(decompress_data)
            print("MAGIC_COMPRESS_START1")
        else:
            pass

            # _outbuffer.extend('seq:%d, hour:%d-%d len:%d decompress:%d\n' %(seq, ord(begin_hour), ord(end_hour), length, len(tmpbuffer)))
    except Exception as e:
        _outbuffer.extend("[F]decode_log_file.py decompress err, " + str(e) +
                          "\n")
        return int(_offset) + int(headerLen) + length + 1

    _outbuffer.extend(tmpbuffer)

    return _offset + headerLen + length + 1


def ParseFile(_file, _outfile):
    fp = open(_file, "rb")
    _buffer = bytearray(os.path.getsize(_file))
    fp.readinto(_buffer)
    fp.close()
    startpos = GetLogStartPos(_buffer, 2)
    if -1 == startpos:
        return

    outbuffer = bytearray()

    while True:
        startpos = DecodeBuffer(_buffer, startpos, outbuffer)
        if -1 == startpos: break

    if 0 == len(outbuffer): return

    fpout = open(_outfile, "wb")
    fpout.write(outbuffer)
    fpout.close()


def DecompressFile(file, outfile):
    dec = zlib.decompressobj(-zlib.MAX_WBITS)
    fin = open(file, "rb")
    fout = open(outfile, "wb")
    buffer = fin.read(IO_BUFFER_SIZE)
    while buffer:
      decompressed = dec.decompress(buffer)
      buffer = fin.read(IO_BUFFER_SIZE)
      fout.write(decompressed)
    decompressed = dec.flush()
    fout.write(decompressed)
    fout.close()
    fin.close()
    print(outfile)

def processfolder(folder, recursive_level):
  if(recursive_level<=0):
    return
  filelist = glob.glob(folder + "/*.clog")
  for file in filelist:
    DecompressFile(file, os.path.splitext(file)[0] + '.log')
  subfolders = glob.glob(folder + "/*/")
  for folder in subfolders:
    processfolder(folder, recursive_level-1)

def process(arg):
  if(arg.endswith('.clog') and os.path.isfile(arg)):
    DecompressFile(arg, os.path.splitext(arg)[0] + '.log')
  elif(os.path.isdir(arg)):
    processfolder(arg, recursive_level)

def main(args):
    global lastseq

    if 1 == len(args):
        if os.path.isdir(args[0]):
            filelist = glob.glob(args[0] + "/*.xlog")
            for filepath in filelist:
                lastseq = 0
                ParseFile(filepath, filepath + ".log")
            filelist = glob.glob(args[0] + "/*.clog")
            for filepath in filelist:
                lastseq = 0
                process(filepath)
        else:
            ParseFile(args[0], args[0] + ".log")
            process(args[0])
    elif 2 == len(args):
        ParseFile(args[0], args[1])
        process(filepath)
    else:
        filelist = glob.glob("*.xlog")
        for filepath in filelist:
            lastseq = 0
            ParseFile(filepath, filepath + ".log")
        filelist = glob.glob("*.clog")
        for filepath in filelist:
            lastseq = 0
            process(filepath)

if __name__ == "__main__":
    main(sys.argv[1:])
