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



# Test algorithm in script:

# 1. Test normal exchange
# 		- Set equal parameters for Master and Slave.
# 		- Send request from Master to Slave.
# 		- Check Master's and Slave's errors.

# 2. Test Slave
#		- Configure Slave with predefined parameters/
# 		- Configure mb_0x6_sender module with Slave parameters 
#		  except random CRC, not equal to correct CRC.
# 		- Start mb_0x6_sender module.
#		- mb_0x6_sender module sends 'request' frame to Slave.
#		- Check Slave's CRC errors. 
	
# 3. Test normal exchange

# 4. Test Master
#	 	- Set equal CRCs for Master and Slave.
# 		- Configure mb_0x6_sender module with random CRC
#		  not equal to correct CRC, and connect it to Master.
# 		- Send request from Master to Slave.
# 		- mb_0x6_sender module sends 'response' frame to Master.
# 		- Unconnect mb_0x6_sender module from Master.
# 		- Check Master's CRC error. 

# 5. Test normal exchange
	
# 6. Display test result.



import mb_bsp
import mb_util
import time
from random import randrange


RAND_TEST_SIZE = 1

# Constants
WAIT_TIME = 0.5 # [seconds]


error_count = 0

		
		
def norm_exch_test(slave_addr, fcode, addr, regnum, regval, speed, conf_bit):		
	print('Run test for slave:')

	mb_bsp.reset_error_count()
	
	# Generate request PDU
	if fcode == 3:
		pdu_l = mb_util.generate_0x03_pdu(addr, regnum)
	elif fcode == 6:
		pdu_l = mb_util.generate_0x06_pdu(addr, regval)
	elif fcode == 16:
		pdu_l = mb_util.generate_0x10_pdu(addr, regnum, regval)
	
	request_pdu = pdu_l[0]
	
	master_config_val = (conf_bit[0] << 8) | speed[0]
	slave_config_val = (conf_bit[1] << 8) | speed[1]
	
	# Configure Modbus master and slave
	mb_util.config_modbus('Master', slave_addr[0], request_pdu, master_config_val)
	mb_util.config_modbus('Slave', slave_addr[1], request_pdu, slave_config_val)
	
	# Send generated PDU
	mb_bsp.write_mb_master_cs(mb_util.CS_REG, 0)
	
	# Wait while master FSM is busy
	mb_util.wait_mb_master_status('FSM status')
	
	# Check if response received
	response_received = mb_bsp.get_pdu_status('Master', 'PDU status')	
	if response_received:
		print('Response received')
	else:
		print('Response isn\'t received')
	
	mb_util.print_error_count()	



def run_test_s_crc(speed, conf_bit):		
	print('Run test for slave:')

	mb_bsp.reset_error_count()
	
	slave_config_val = (conf_bit[1] << 8) | speed[1]
	
	# Configure Modbus slave
	mb_util.config_modbus('Slave', 1, [], slave_config_val)
		
	# Configure mb_0x6_sender module 
	true_crc = 0xCA89
	fake_crc = randrange(0, 65536)
	while fake_crc == true_crc:
		fake_crc = randrange(0, 65536)
	mb_bsp.mb_test_set_configure(	1, 			# slave_addr
									(conf_bit[1] & 0x4) >> 2, 			# stop_bits
									conf_bit[1] & 0x1, 			# parity_ena
									(conf_bit[1] & 0x2) >> 1,			# parity_type
									speed[1],			# speed
									0,			# reg_addr
									0,			# reg_val
									fake_crc)		# crc
	
	# Trigger mb_0x6_sender module to send frame
	mb_bsp.mb_test_frame_start()
	
	# Wait while Slave process request
	time.sleep(WAIT_TIME)
	
	mb_util.print_error_count()	

	
		
def run_test_m_crc(speed, conf_bit):		
	print('Run test for master:')

	mb_bsp.reset_error_count()

	# Generate request PDU
	pdu_l = mb_util.generate_0x06_pdu(0, [0])
	
	request_pdu = pdu_l[0]
	
	master_config_val = (conf_bit[0] << 8) | speed[0]
	
	# Configure Modbus master and slave
	mb_util.config_modbus('Master', 1, request_pdu, master_config_val)
	mb_util.config_modbus('Slave', 1, request_pdu, master_config_val)
	
	# Configure mb_0x6_sender module 
	true_crc = 0xCA89
	fake_crc = randrange(0, 65536)
	while fake_crc == true_crc:
		fake_crc = randrange(0, 65536)
	mb_bsp.mb_test_set_configure(	1, 			# slave_addr
									(conf_bit[0] & 0x4) >> 2, 			# stop_bits
									conf_bit[0] & 0x1, 			# parity_ena
									(conf_bit[0] & 0x2) >> 1,			# parity_type
									speed[0],			# speed
									0,			# reg_addr
									0,			# reg_val
									fake_crc)		# crc
									
	# Connect mb_0x6_sender module to modbus_rtu_master
	mb_bsp.mb_test_select(1)
	
	# Send generated PDU
	mb_bsp.write_mb_master_cs(mb_util.CS_REG, 0)
	
	# Wait while master FSM is busy
	mb_util.wait_mb_master_status('FSM status')
	
	# Check if response received
	response_received = mb_bsp.get_pdu_status('Master', 'PDU status')	
	if response_received:
		print('Response received')
	else:
		print('Response isn\'t received')

	# Unconnect mb_0x6_sender module from modbus_rtu_master
	mb_bsp.mb_test_select(0)
	
	mb_util.print_error_count()	
	
	

def run_tests():
	global error_count;

	print()
	print('*** Start CRC test ***')
	
	mb_bsp.reset_error_count()
	
	# Generate regnum 
	regnum = 1
	print('regnum = ', regnum)
	
	# Generate Modbus register values
	regval = [0]
	print('regval = ', regval)
		
	# Generate baud rate list
	speed_rate = randrange(0, 4)
	speed = [speed_rate, speed_rate]
	print('speed = ', speed)
	
	# Set configuration bits to avoid parity error checks
	conf_bit = [0, 0]
	print('conf_bit = ', conf_bit)	
	
	# Generate slave address for master and for slave
	addr = [1, 1]
	print('addresses = ', addr)
	
	# Do transaction and check error counters
	print('Start normal exchange')
	norm_exch_test(addr, mb_util.FCODE_0x6, 0, regnum, regval, speed, conf_bit)
	if	mb_util.get_total_error_count('Both') > 0 \
		or mb_util.incr_err_count.count > 0:
		error_count += 1
		print('DEBUG: norm_exch_test')
	
	for i in range(RAND_TEST_SIZE):
		run_test_s_crc(speed, conf_bit)
		if	mb_util.get_single_error_count('Slave', 'crc') == 0 \
			or	mb_util.get_total_error_count('Master') > 0 \
			or	mb_util.incr_err_count.count > 0:
			error_count += 1
			print('DEBUG: run_test_s_crc')
		
	print('Start normal exchange')		
	norm_exch_test(addr, mb_util.FCODE_0x6, 0, regnum, regval, speed, conf_bit)
	if	mb_util.get_total_error_count('Both') > 0 \
		or	mb_util.incr_err_count.count > 0:
		error_count += 1
		print('DEBUG: norm_exch_test')
		
	for i in range(RAND_TEST_SIZE):
		run_test_m_crc(speed, conf_bit)
		if	mb_util.get_total_error_count('Slave') > 0 \
			or mb_util.get_single_error_count('Master', 'crc') == 0 \
			or	mb_util.incr_err_count.count > 0:
			error_count += 1
			print('DEBUG: run_test_m_crc')
	
	print('Start normal exchange')		
	norm_exch_test(addr, mb_util.FCODE_0x6, 0, regnum, regval, speed, conf_bit)
	if	mb_util.get_total_error_count('Both') > 0 \
		or mb_util.incr_err_count.count > 0:
		error_count += 1
		print('DEBUG: norm_exch_test')

	print('Timeout error count = ', mb_util.incr_err_count.count)
	

	mb_util.print_test_result(error_count == 0)
	
	
run_tests()
