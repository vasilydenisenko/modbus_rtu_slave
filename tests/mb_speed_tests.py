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

# 1. Select baud rate pair from the set of all combinations.

# 2. Test Master and Slave
#		- Set baud rates for Master and Slave.
#		- Send request from Master to Slave.
#		- If baud rates are equal, 
#			check Master's and Slave's errors, 
#			else check Slave's errors.
	
# 3. Test Master
#		- Set equal baud rates for Master and Slave.
# 		- Configure mb_0x6_sender module with baud rate different from Master's one, 
# 		  and connect it to Master.
#		- Send request from Master to Slave.
#		- mb_0x6_sender module sends 'response' frame to Master.
#		- Unconnect mb_0x6_sender module from Master.
#		- Check Master's errors. 
	
# 4. If all baud rate pair combinations passed, display test result.



import mb_bsp
import mb_util
from random import randrange



error_count = 0


def run_test_s_speed(slave_addr, fcode, addr, regnum, regval, speed, conf_bit):	
	print('Run test for slave:')
	
	mb_bsp.reset_error_count()
	
	# Generate request PDU
	if fcode == mb_util.FCODE_0x3:
		pdu_l = mb_util.generate_0x03_pdu(addr, regnum)
	elif fcode == mb_util.FCODE_0x10:
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





def run_test_m_speed(speed, conf_bit):	
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
	mb_bsp.mb_test_set_configure(	1, 			# slave_addr
									(conf_bit[0] & 0x4) >> 2, 			# stop_bits
									conf_bit[0] & 0x1, 			# parity_ena
									(conf_bit[0] & 0x2) >> 1,			# parity_type
									speed[1],			# speed
									0,			# reg_addr
									0,			# reg_val
									true_crc)		# crc
	
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
	print('*** Start speed test ***')
	
	mb_bsp.reset_error_count()
	
	# Generate speed list to select from
	speed_l = [i for i in range(4)]
	
	# Generate slave address (1...247) for master and for slave
	address = randrange(1, mb_util.MB_MAX_SLAVE_ADDR + 1)
	addr = [address, address]
	print('addresses = ', addr)

	# Generate slave regnum (1...123)
	regnum_slave = randrange(1, mb_util.MB_MAX_WRITE_REGNUM + 1)
	print('regnum_slave = ', regnum_slave)
	print('regnum_master = ', mb_util.MB_MAX_WRITE_REGNUM)	

	
	# Generate Modbus register values	
	regval_master = [randrange(0, mb_util.MB_MAX_REG_VAL + 1)]
	regval_slave = [randrange(0, mb_util.MB_MAX_REG_VAL + 1) for i in range(regnum_slave)]
	
	# Set configuration bits to avoid parity error checks
	conf_bit = [0, 0]
	
	# Select master's speed
	for i in range(len(speed_l)):
		master_speed = speed_l[i]
		
		# Select slave's speed
		for j in range(len(speed_l)):
			slave_speed = speed_l[j]
			
			print('master_speed = ', master_speed, '; slave_speed = ', slave_speed)
			
			speed = [master_speed, slave_speed]
			
			# Do transaction and check error counters
			run_test_s_speed(addr, mb_util.FCODE_0x10, 0, regnum_slave, regval_slave, speed, conf_bit)
			if master_speed == slave_speed:
				if	mb_util.get_total_error_count('Both') > 0 \
					or	mb_util.incr_err_count.count > 0:
					error_count += 1
			else:
				if	mb_util.get_total_error_count('Slave') == 0 \
					or	mb_util.get_total_error_count('Master') > 0 \
					or	mb_util.incr_err_count.count > 0:
					error_count += 1
			
				run_test_m_speed(speed, conf_bit)
				if	mb_util.get_total_error_count('Slave') > 0 \
					or mb_util.get_total_error_count('Master') == 0 \
					or	mb_util.incr_err_count.count > 0:
					error_count += 1
	

	print('Timeout error count = ', mb_util.incr_err_count.count)
	
	mb_util.print_test_result(error_count == 0)				

	
	

run_tests()

