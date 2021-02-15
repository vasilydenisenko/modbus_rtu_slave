# MIT License

# Copyright (c) 2021 Vasily Denisenko, Sergey Kuznetsov

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.



import mb_bsp



PDU_SIZE_REG = 0
CONFIG_REG = 1
SLAVE_ADDR_REG = 2
CS_REG = 3

MB_MAX_WRITE_REGNUM = 123
MB_MAX_READ_REGNUM = 125
MB_MAX_REG_ADDR = 65535
MB_MAX_REG_VAL = 65535
MB_MAX_SLAVE_ADDR = 247
MB_MIN_SLAVE_ADDR = 1
MB_MAX_PDU_SIZE = 253
MB_MIN_PDU_SIZE = 1

FCODE_0x3 = 0x3
FCODE_0x6 = 0x6
FCODE_0x10 = 0x10



def incr_err_count():
	incr_err_count.count += 1
	
setattr(incr_err_count, 'count', 0)



def wait_mb_master_status(status):
	mb_bsp.wait_master_status(status)  # 'FSM status' or 'PDU status'
	if mb_bsp.alarm_cb.status_timeout == 1:
		print('*** Test FAILED: ', status , ' timeout ***') 
		mb_bsp.alarm_cb.status_timeout = 0
		incr_err_count()


	
def config_modbus(modbus_role, slave_addr, pdu, config_val):
	wait_mb_master_status('FSM status')

	if modbus_role == 'Master':
		mb_bsp.write_mb_master_cs(CONFIG_REG, config_val)		# Set configuration
		mb_bsp.write_mb_master_cs(SLAVE_ADDR_REG, slave_addr)	# Set slave address
		mb_bsp.write_mb_master_cs(PDU_SIZE_REG, len(pdu))		# Set request PDU size
			
		mb_bsp.write_mb_master_pdu(pdu)						# Set request PDU
	else:
		mb_bsp.write_mb_slave_cs(CONFIG_REG, config_val)		# Set configuration
		mb_bsp.write_mb_slave_cs(SLAVE_ADDR_REG, slave_addr)	# Set slave address



def generate_0x03_pdu(addr, regnum):
	pdu = list()
	ref_pdu = list()
	pdu.append(0x3)
	ref_pdu.append(0x3)
	
	addr_h = (addr & 0xff00) >> 8
	pdu.append(addr_h)
	addr_l = (addr & 0xff)
	pdu.append(addr_l)

	regnum_h = (regnum & 0xff00) >> 8
	pdu.append(regnum_h)
	regnum_l = regnum & 0xff
	pdu.append(regnum_l)
	bytecount = regnum << 1
	ref_pdu.append(bytecount)
	for i in range(bytecount):
		ref_pdu.append(0)	
	
	return [pdu, ref_pdu]
	

	
def generate_0x06_pdu(addr, regval):
	pdu = list()
	pdu.append(0x6)

	addr_h = (addr & 0xff00) >> 8
	pdu.append(addr_h)
	addr_l = (addr & 0xff)
	pdu.append(addr_l)
	
	regval_h = (regval[0] & 0xff00) >> 8
	pdu.append(regval_h)
	regval_l = regval[0] & 0xff
	pdu.append(regval_l)
	
	ref_pdu = pdu.copy()
	
	return [pdu, ref_pdu]	



def generate_0x10_pdu(addr, regnum, regval):
	pdu = list()
	pdu.append(0x10)
	
	addr_h = (addr & 0xff00) >> 8
	pdu.append(addr_h)
	addr_l = (addr & 0xff)
	pdu.append(addr_l)
	
	regnum_h = (regnum & 0xff00) >> 8
	pdu.append(regnum_h)
	regnum_l = regnum & 0xff
	pdu.append(regnum_l)
	
	ref_pdu = pdu.copy()
	
	bytecount = regnum_l << 1
	pdu.append(bytecount)
	
	for i in range(regnum_l):
		regval_h = (regval[i] & 0xff00) >> 8
		pdu.append(regval_h)
		regval_l = regval[i] & 0xff
		pdu.append(regval_l)
		
	return [pdu, ref_pdu]
	
	
	
def print_test_result(result_ok):
	if result_ok:
		msg = '\tTest Successful'
	else:
		msg = '\tTest FAILED'
	
	print()	
	print('***************************')
	print(msg)
	print('***************************')
	print()
		
		

def get_total_error_count(modbus_role):
	count = 0
	error_tuple = mb_bsp.get_error_count()
	if modbus_role == 'Both':
		for err_list in error_tuple:
			for i in err_list:
				count += i
	elif modbus_role == 'Master':
		for i in error_tuple[0]:
			count += i
	elif modbus_role == 'Slave':
		for i in error_tuple[1]:
			count += i
		
	return count
	


def get_single_error_count(modbus_role, error_type):
	error_tuple = mb_bsp.get_error_count()
	count = 0
	if modbus_role == 'Master':
		if error_type == 'parity':
			count = error_tuple[0][0]
		elif error_type == 'start bit':
			count = error_tuple[0][1]
		elif error_type == 'stop bit':
			count = error_tuple[0][2]
		elif error_type == 'address':
			count = error_tuple[0][3]
		elif error_type == 'crc':
			count = error_tuple[0][4]
	elif modbus_role == 'Slave':
		if error_type == 'parity':
			count = error_tuple[1][0]
		elif error_type == 'start bit':
			count = error_tuple[1][1]
		elif error_type == 'stop bit':
			count = error_tuple[1][2]
		elif error_type == 'address':
			count = error_tuple[1][3]
		elif error_type == 'crc':
			count = error_tuple[1][4]
	
	return count
		
	
	
def print_error_count():	
	error_tuple = mb_bsp.get_error_count()

	print()	
	print('master_parity_err_count = ', error_tuple[0][0])
	print('master_start_bit_err_count = ', error_tuple[0][1])
	print('master_stop_bit_err_count = ', error_tuple[0][2])
	print('master_addr_err_count = ', error_tuple[0][3])
	print('master_crc_err_count = ', error_tuple[0][4])

	print('slave_parity_err_count = ', error_tuple[1][0])
	print('slave_start_bit_err_count = ', error_tuple[1][1])
	print('slave_stop_bit_err_count = ', error_tuple[1][2])
	print('slave_addr_err_count = ', error_tuple[1][3])
	print('slave_crc_err_count = ', error_tuple[1][4])
	
	print('--------------------------------')
	print()	
	