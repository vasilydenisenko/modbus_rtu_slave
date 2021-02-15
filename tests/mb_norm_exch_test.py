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
 
# 1. Select and write functional code (0x3, 0x10), baud rate and 
#	 configuration bits from the set of all valid combinations.
# 2. Write valid random regnum (including maximum possible), address and 
#	 register values.
# 3. Generate request and reference response frames.
# 4. Send request.
# 5. Check if response is equal to reference response



import mb_bsp
import mb_util
from random import randrange



RAND_TEST_SIZE = 1



def run_test_positive(slave_addr, fcode, addr, regnum, regval, speed, conf_bit):	
	# Generate request PDU and reference response PDU
	if fcode == 3:
		pdu_l = mb_util.generate_0x03_pdu(addr, regnum)
	elif fcode == 16:
		pdu_l = mb_util.generate_0x10_pdu(addr, regnum, regval)
	
	request_pdu = pdu_l[0]
	ref_pdu = pdu_l[1]
	
	master_config_val = (conf_bit[0] << 8) | speed[0]
	slave_config_val = (conf_bit[1] << 8) | speed[1]
	
	# Configure Modbus master and slave
	mb_util.config_modbus('Master', slave_addr[0], request_pdu, master_config_val)
	mb_util.config_modbus('Slave', slave_addr[1], request_pdu, slave_config_val)
	
	# Send generated PDU
	mb_bsp.write_mb_master_cs(mb_util.CS_REG, 0)

	if slave_addr[0] != 0:	# unicast
		# Wait for master response is received
		mb_util.wait_mb_master_status('PDU status')
		if mb_util.incr_err_count.count > 0:
			return
			
		pdu_size = mb_bsp.read_mb_master_cs(mb_util.PDU_SIZE_REG)		# Get response PDU size
		response_pdu = mb_bsp.read_mb_master_pdu(pdu_size)		# Get response PDU
	
		if fcode == 3:
			pdu_mismatch = ref_pdu[0:2] != response_pdu[0:2] or len(ref_pdu) != len(response_pdu)
		else:
			pdu_mismatch = ref_pdu != response_pdu
		
		# Process response PDU
		if pdu_mismatch:
			print('*** Unicast test FAILED: Response PDU is not valid ***')
			mb_util.incr_err_count()
			response_pdu_size = len(response_pdu)
			size_isnt_divisible = response_pdu_size & 0x1
			if size_isnt_divisible:
				response_pdu_size -= 1
			print('Reference PDU:')
			for i in range(len(ref_pdu)):
				print(f'{ref_pdu[i]:#d}')
			print('Response PDU:')
			for i in range(pdu_size):
				print(f'{response_pdu[i]:#d}')
	else:	# broadcast
		# Wait for master FSM is ready
		mb_bsp.wait_master_status('FSM status') 
		
		if mb_bsp.alarm_cb.status_timeout == 1:
			print('*** Broadcast test FAILED: FSM status timeout ***') 
			mb_bsp.alarm_cb.status_timeout = 0
			mb_util.incr_err_count()
			return
		else:		
			response_received = mb_bsp.get_pdu_status('Master', 'PDU status')		
			if response_received:
				print('*** Broadcast test FAILED: Broadcast reply is received ***')
				mb_util.incr_err_count()
				return
		
		if fcode == 16:
			slave_regval = mb_bsp.direct_read_mb_slave_reg(addr, regnum)
			if regval != slave_regval:
				print('*** Broadcast test FAILED: Response PDU is not valid ***')
				mb_util.incr_err_count()
				print('regval = ', regval)
				print('slave_regval = ', slave_regval)
	


def run_tests():
	print()
	print('*** Start normal exchange test ***')
	
	mb_bsp.reset_error_count()
	
	# Generate frame parameters to select from
	fcode_l = [mb_util.FCODE_0x3, mb_util.FCODE_0x10]
	speed_l = [i for i in range(4)]
	conf_bit_l = [i for i in range(8)] 
	maxregnum_l = [mb_util.MB_MAX_READ_REGNUM, mb_util.MB_MAX_WRITE_REGNUM]
		
	# Select request's fcode (0x3, 0x10)
	for i in range(len(fcode_l)):
		fcode = fcode_l[i]
		
		# Select speed rate (0...3) for master and for slave
		for j in range(len(speed_l)):
			speed = [speed_l[j], speed_l[j]]
	
			# Select parity enable, parity type and stop bits (0...7)
			for k in range(len(conf_bit_l)):
				conf_bit = [conf_bit_l[k], conf_bit_l[k]]

				print('fcode = ', fcode, '; speed = ', speed, '; conf_bit = ', conf_bit)

				# Step through test sample
				for l in range(RAND_TEST_SIZE):
					# Generate regnum (1...123/125)
					regnum = randrange(1, maxregnum_l[i] + 1)
					print('regnum = ', regnum)
					
					# Generate slave address (1...247) for master and for slave
					address = randrange(1, mb_util.MB_MAX_SLAVE_ADDR + 1)
					addr = [address, address]
					print('addresses = ', addr)
					
					# Generate Modbus register values
					regval = [randrange(0, mb_util.MB_MAX_REG_VAL + 1) for i in range(regnum)]
					
					# Do transaction and check response
					run_test_positive(addr, fcode, 0, regnum, regval, speed, conf_bit)
					
					# Set addresses for broadcast exchange 
					addr = [0, address]
					print('addresses = ', addr)
					
					# Do transaction and check response
					run_test_positive(addr, fcode, 0, regnum, regval, speed, conf_bit) 
				
				print()	
	
	print('Full PDU size tests')
	print()
	
	# Set addresses for unicast exchange
	addr = [address, address]
	print('fcode = ', mb_util.FCODE_0x3, '; speed = ', speed, '; conf_bit = ', conf_bit)
	print('regnum = ', mb_util.MB_MAX_READ_REGNUM)
	print('addresses = ', addr)
	
	# Do transaction with 0x03 function code and check response
	run_test_positive(addr, mb_util.FCODE_0x3, 0, mb_util.MB_MAX_READ_REGNUM, regval, speed, conf_bit)
	
	print('fcode = ', mb_util.FCODE_0x10, '; speed = ', speed, '; conf_bit = ', conf_bit)
	print('regnum = ', mb_util.MB_MAX_WRITE_REGNUM)
	print('addresses = ', addr)
	
	# Prepare register values for 0x10 function code
	regval = [randrange(0, mb_util.MB_MAX_REG_VAL + 1) for i in range(mb_util.MB_MAX_WRITE_REGNUM)]
	
	# Do transaction with 0x10 function code and check response
	run_test_positive(addr, mb_util.FCODE_0x10, 0, mb_util.MB_MAX_WRITE_REGNUM, regval, speed, conf_bit)

	mb_util.print_error_count()
	
	print('Timeout error count = ', mb_util.incr_err_count.count)
	
	
	result_ok = 	mb_util.get_total_error_count('Both') == 0 \
					and mb_util.incr_err_count.count == 0
	mb_util.print_test_result(result_ok)



	
run_tests()
