import ctypes
import numpy as np

def h2i(s):
    '''hex to int'''
    cp = ctypes.pointer(ctypes.c_longlong(s))
    fp = ctypes.cast(cp, ctypes.POINTER(ctypes.c_int))
    # print(cp, fp)
    # print(fp.contents.value)
    return fp.contents.value

def h2i8(s):
    '''hex to int8'''
    cp = ctypes.pointer(ctypes.c_longlong(s))
    fp = ctypes.cast(cp, ctypes.POINTER(ctypes.c_int8))
    # print(cp, fp)
    # print(fp.contents.value)
    return fp.contents.value

def h2ui(s):
    '''hex to uint'''
    cp = ctypes.pointer(ctypes.c_longlong(s))
    fp = ctypes.cast(cp, ctypes.POINTER(ctypes.c_uint))
    # print(cp, fp)
    # print(fp.contents.value)
    return fp.contents.value

def h2ui8(s):
    '''hex to uint8'''
    cp = ctypes.pointer(ctypes.c_longlong(s))
    fp = ctypes.cast(cp, ctypes.POINTER(ctypes.c_uint8))
    # print(cp, fp)
    # print(fp.contents.value)
    return fp.contents.value

def h2f(s):
    '''hex to float'''
    cp = ctypes.pointer(ctypes.c_longlong(s))
    fp = ctypes.cast(cp, ctypes.POINTER(ctypes.c_float))
    # print(cp, fp)
    # print(fp.contents.value)
    return fp.contents.value

def h2d(s):
    '''hex to double'''
    cp = ctypes.pointer(ctypes.c_longlong(s))
    fp = ctypes.cast(cp, ctypes.POINTER(ctypes.c_double))
    # print(cp, fp)
    # print(fp.contents.value)
    return fp.contents.value

_MAP = {
    'U8': h2ui8,
    'U16': h2ui,
    'U32': h2ui,
    'S8': h2i8,
    'S16': h2i,
    'S32': h2i,
    'FLOAT': h2f,
    'DOUBLE': h2d
}

def formatData(data):

    # _bin = bin(int(data, 8))
    _oct = oct(int(data, 2))
    _int = int(data, 2)
    _hex = hex(int(data, 2))

    print(_oct, _int, _hex)
    return _oct, _int, _hex

def dfFormat(data, logger):
    '''dataFrame data列转化10进制'''
    try:
        for _, row in data.iterrows():
            _addr = row['Addr']
            _type = row['type']
            _size = int(row['size'])

            _data = list(filter(None, row['data'].split(' ')))

            if len(_data) == _size:
                _data = [int(a, 16) for a in _data]
                f_data = dataTrans(_data, _type, logger)
                # row['data'] = str(_data).replace('[', '').replace(',', '').replace(']', '')
                row['data'] = str(f_data).replace('[', '').replace(',', '').replace(']', '')
        # print(data)
        return data
    except Exception as e:
        logger.exception(e)
        return None

def formatPlotData(data, _type, _size, logger):
    '''数据绘图 data转换'''
    try:
        func = _MAP[_type]
        f_data = []
        _data = list(filter(None, data.split(' ')))
        if len(_data) == _size:
            _data = [int(a, 16) for a in _data]
            for i in _data:
                _d = func(i)
                f_data.append(_d)
            return f_data
    except Exception as e:
        logger.exception(e)
        return None

def dataTrans(data, _type, logger):
    try:
        func = _MAP[_type]
        f_data = []
        for i in data:
            _d = func(i)
            f_data.append(_d)
        return f_data
    except Exception as e:
        logger.exception(e)
        return None

if __name__ == '__main__':
    formatData(data=b'0001')
    # formatData(data=0011)
    formatData(data=b'0001100010')
    # print(hex(4294967295)) # 0xffff ffff
    print(int('0xffffffff', 16))