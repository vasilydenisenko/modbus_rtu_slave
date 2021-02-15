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



import mb_util
import time
import threading



TIMEOUT = 5 # sec




def alarm_cb(msg):	
	alarm_cb.status_timeout = 1
	print(time.ctime(), ': *** ', msg, ' ***')	

setattr(alarm_cb, 'status_timeout', 0)




def read_mb_master_cs(cs_reg):
	# Type here your implementation based on your hardware
	
	return rdata
	
	


def write_mb_master_cs(cs_reg, wdata):
	# Type here your implementation based on your hardware


def read_mb_slave_cs(cs_reg):
	# Type here your implementation based on your hardware
	
	return rdata


def write_mb_slave_cs(cs_reg, wdata):
	# Type here your implementation based on your hardware
		


def read_mb_master_pdu(size):
	# Type here your implementation based on your hardware
	
	return reply
		
		
		
def write_mb_master_pdu(wdata):
	# Type here your implementation based on your hardware
			

		
def wait_master_status(status):
	# Type here your implementation based on your hardware
		
				

def get_pdu_status(modbus_role, status):
	# Type here your implementation based on your hardware
		
	return stat

	

def direct_read_mb_slave_reg(addr, regnum):
	# Type here your implementation based on your hardware
	
	return rdd_list



	
def get_error_count():
	# Type here your implementation based on your hardware
	
	return (master_list, slave_list)

	
	
def reset_error_count():
	# Type here your implementation based on your hardware
	
	print('Error counters are reset')
	


def mb_test_select(selector):
	# Type here your implementation based on your hardware
	
	print('Modbus select set to ', selector)
	
	
	
def mb_test_frame_start():
	# Type here your implementation based on your hardware

	print('Send test frame')
	
	
def mb_test_set_configure(	slave_addr, 
							stop_bits, 
							parity_ena, 
							parity_type,
							speed,
							reg_addr,
							reg_val,
							crc):
	print('Set fcode 0x06 test frame parameters configuration:')
	# Type here your implementation based on your hardware
	print('slave_addr = ', slave_addr)
	print('stop_bits = ', stop_bits)
	print('parity_ena = ', parity_ena)
	print('parity_type = ', parity_type)
	print('speed = ', speed)
	print('reg_addr = ', reg_addr)
	print('reg_val = ', reg_val)
	print(f'crc = {crc:#x}')
	



