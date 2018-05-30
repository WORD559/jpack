##Object to pack data into binary files

from math import ceil
import os

class LengthError(Exception):
    pass

class packer(object):
    ##--Datatypes--
    ##
    ## 0 = integer
    ## 1 = string
    ## 2 = array
    ## 3 = float
    ## 4 = None
    ## 5 = Negative Integer
    ## 6 = Negative Float
    def __init__(self,filepath):
        """Packer object"""
        self.f = filepath

    def fix_headers(self):
        temp = open(os.path.abspath(self.f)[:-len(os.path.basename(os.path.abspath(self.f)))]+"temp","wb")
        f = open(self.f,"rb")
        temp.write("JPK")
        temp.write(f.read(1048576))
        temp.close()
        f.close()
        os.remove(self.f)
        os.rename(os.path.abspath(self.f)[:-len(os.path.basename(os.path.abspath(self.f)))]+"temp",self.f)

    def clear_file(self):
        f = open(self.f,"wb")
        f.write("JPK")
        #f.write(bytearray([0]))
        f.close()

    def delete_array(self,index,hard=True):
        if not hard:
            try:
                while 1:
                    if index == 0:
                        pos = 3
                        if len(self.read()) == 1:
                            self.clear_file()
                            return None
                    else:
                        #print index-1
                        pos = self.read(index-1,return_position=True)[1]
                        print pos
                        

                    data = self.read(index+1,return_position=True)[0]
                    #print data
                    if data == "":
                        break
                    data = self.write_array(data,False,True)
                    f = open(self.f,"r+b")
                    f.seek(pos)
                    f.write(data)   
                    index += 1
                #print "truncating after",pos
                f.truncate()
            except KeyboardInterrupt:
                f.close()
        else:
            temp = packer(os.path.abspath(self.f)[:-len(os.path.basename(os.path.abspath(self.f)))]+"temp")
            data = self.read()
            for i in range(len(data)):
                if i != index:
                    temp.write_array(data[i])
            os.remove(self.f)
            os.rename(os.path.abspath(self.f)[:-len(os.path.basename(os.path.abspath(self.f)))]+"temp",self.f)


    def write_array(self,array,write=True,return_data=False,mode="ab",array_tag=True,array_length=True,force_write=False):
        """Supports int, str, list, float."""
        data = bytearray()
        if not force_write:
            try:
                if write:
                    f = open(self.f,"r+b")
                    if f.read(3) != "JPK":
                        print "File is not valid JPK file! Confirm overwrite?"
                        if raw_input("(Y/N)? ").upper() == "Y":
                            f.close()
                            f = open(self.f,"wb")
                            f.write("JPK")
                            f.close()
            except:
                if write:
                    f = open(self.f,"wb")
                    f.write("JPK")
                    f.close()
            
        if array_tag:
            data.append(2)
        
        if array_length:
            if len(array) < 255:
                data.append(len(array))
            else:
                raise LengthError("array must have length < 255")

        for thing in array:
            if isinstance(thing, int):
                if thing < 0:
                    data.append(5)
                    thing *= -1
                else:
                    data.append(0)
                length = len(bin(thing)[2:])
                len_bytes = int(ceil(length/8.))
                data.append(len_bytes)
                binary = bin(thing)[2:]
                while len(binary)%8 != 0:
                    binary = "0"+binary
                count = 0
                chunk = binary[0:8]
                #print chunk
                while chunk != "":
                    data.append(int(chunk,2))
                    count += 1
                    chunk = binary[count*8:(count+1)*8]
                    #print chunk
            elif isinstance(thing,list):
                data+=(self.write_array(thing,False,True))
            elif isinstance(thing,str):
                data.append(1)
                binary = ""
                bins = ""
                for char in thing:
                    bins+= bin(ord(char))[2:]
                    while len(bins)%8 != 0:
                        bins = "0"+bins
                    #print bins
                    binary+=bins
                    bins = ""
                data.append(len(binary)/8)
                count = 0
                chunk = binary[0:8]
                #print chunk
                while chunk != "":
                    data.append(int(chunk,2))
                    count += 1
                    chunk = binary[count*8:(count+1)*8]
                    #print chunk
            elif isinstance(thing,float):
                if thing < 0:
                    data.append(6)
                    thing *= -1
                else:
                    data.append(3)
                count = 0
                while int(thing) != thing:
                    count += 1
                    thing *= 10
                thing = int(thing)
                arrayed = [thing,count]
                
                length = len(bin(arrayed[0])[2:])
                len_bytes = int(ceil(length/8.))
                data.append(len_bytes)
                binary = bin(arrayed[0])[2:]
                while len(binary)%8 != 0:
                    binary = "0"+binary
                count = 0
                chunk = binary[0:8]
                #print chunk
                while chunk != "":
                    data.append(int(chunk,2))
                    count += 1
                    chunk = binary[count*8:(count+1)*8]
                    #print chunk
                data.append(arrayed[1])
            elif thing == None:
                data.append(4)
                
            else:
                raise ValueError("'"+type(thing).__name__+"' not supported")

        if write:
            f = open(self.f,mode)
            f.write(data)
            f.close()
        if return_data:
            return data

    def read(self,files=None,start=3,return_position=False,force_read=False):
        f = open(self.f,"rb")
        if (f.read(3) != "JPK") and not force_read:
            raise TypeError("File is not a valid JPK file!")
        if force_read == True:
            start=0
        pos = start
        data = []
        returned = None
        count = 0
        while returned != "":
            returned, pos = (self.__readdata__(pos,True))
            if files == None:
                data.append(returned)
            elif count == files:
                if return_position:
                    return (returned,pos)
                else:
                    return returned
            count += 1
        try:
            data.pop(-1)
        except IndexError:
            pass
        if return_position:
            return (data,pos)
        else:
            return data

    def __readdata__(self,start=3,return_position=False):
        LENGTHLESS = [4]
        f = open(self.f,"rb")
        f.seek(start)
        r = f.read(1)
        if r == "":
            return ("",f.tell())
        datatype = int(r.encode("hex"),16)
        
        if datatype not in LENGTHLESS:
            r = f.read(1)
            length = int(r.encode("hex"),16)
        
        if datatype == 0:
            #print "int"
            r = f.read(length)
            data = int(r.encode("hex"),16)

        if datatype == 5:
            r = f.read(length)
            data = int(r.encode("hex"),16)*-1
            
        if datatype == 1:
            #print "string"
            data = ""
            r = f.read(length)
            binary = bin(int(r.encode("hex"),16))[2:]
            while len(binary)%8 != 0:
                binary = "0"+binary

            count = 0
            chunk = binary[0:8]
            #print chunk
            while chunk != "":
                data+=chr(int(chunk,2))
                count += 1
                chunk = binary[count*8:(count+1)*8]
                #print chunk
            
        if datatype == 2:
            #print "array"
            data = []
            pos = f.tell()
            for x in range(length):
                r, pos = self.__readdata__(pos,True)
                data.append(r)
        if datatype == 3:
            #print "float"
            data = [None,None]
            r = f.read(length)
            data[0] = int(r.encode("hex"),16)
            r = f.read(1)
            data[1] = int(r.encode("hex"),16)
            
            data = data[0]*10**-(data[1])

        if datatype == 6:
            data = [None,None]
            r = f.read(length)
            data[0] = int(r.encode("hex"),16)
            r = f.read(1)
            data[1] = int(r.encode("hex"),16)
            
            data = (data[0]*10**-(data[1]))*-1
            
        if datatype == 4:
            data = None
        if return_position:
            try:
                if pos < f.tell():
                    pos = f.tell()
            except:
                pos = f.tell()
        f.close()
        if return_position:
            return (data,pos)
        else:
            return data

