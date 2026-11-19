"""Exact OpenFreeMap components represented by custom geometry in the HQ area.

Keys: rounded local centre X/Y, source render_height, source min_height, metres.
A different footprint, podium or elevated link must not be masked by proximity.
"""
PARTS={
    (1944.1,684.6,300,0):'CMB/Main tower west outer',
    (1953.6,680.6,340,0):'CMB/Main tower west inner',
    (1971.7,685.1,387,0):'CMB/Main tower central pair',
    (1989.9,680.1,340,0):'CMB/Main tower east inner',
    (1999.4,684.6,300,0):'CMB/Main tower east outer',
    (1924.7,593.2,107,0):'CMB/Lot 2 north',
    (1935.5,593.3,89,0):'CMB/Lot 2 north',
    (1946.0,593.3,72,0):'CMB/Lot 2 north',
    (2019.0,593.2,107,0):'CMB/Lot 3 north',
    (2008.3,593.3,89,0):'CMB/Lot 3 north',
    (1997.7,593.2,72,0):'CMB/Lot 3 north',
    (1924.9,510.5,80,0):'CMB/Lot 2 south',
    (1935.7,510.3,70,0):'CMB/Lot 2 south',
    (1946.3,510.6,58,0):'CMB/Lot 2 south',
    (2018.9,510.2,80,0):'CMB/Lot 3 south',
    (2008.0,510.2,70,0):'CMB/Lot 3 south',
    (1997.5,510.2,56,0):'CMB/Lot 3 south',
    (1814.4,694.5,312,0):'CITIC/T1',
    (1852.5,570.8,200,0):'CITIC/T2',
    (1990.9,867.0,359,0):'Huiyun',
    (2094.6,1115.0,154,0):'Digital China/T1',
    (2203.3,1054.8,147,0):'Digital China/T2',
}

def key(cx,cy,h,lo):
    return round(cx,1),round(cy,1),float(h),float(lo)

def replaces(cx,cy,h,lo):
    return key(cx,cy,h,lo) in PARTS
