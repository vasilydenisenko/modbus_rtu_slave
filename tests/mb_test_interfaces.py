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

# Test Modbus master and then Modbus slave:

# 1. Test Master PDU size register:
#		- Read PDU size register value.
#		- Select and write valid random value to PDU size register.
#		- Check if read value was not modified.

# 2. Test Master Configuration register:
#		- Select and write configuration from the set of all valid combinations.
#		- Check if read value is the same.
#		- If all combinations passed, write random value.
#		- Check if read value is equal to write value,
#		  which masked with register's significant bits.

# 3. Test Slave address register:
#		- Select and write slave address from the set of all valid values.
#		- Check if read value is the same.
#		- If all combinations passed, write non-valid random value.
#		- Check if read value was not modified.



import mb_bsp
import mb_util
from random import randrange

error_count = 0

print('Test Control and status interface for master')
print()

# Test PDU size register
read_pdu_size_cur = mb_bsp.read_mb_master_cs(mb_util.PDU_SIZE_REG)
read_pdu_size_prv = read_pdu_size_cur
random_pdu_size = randrange(mb_util.MB_MIN_PDU_SIZE, mb_util.MB_MAX_PDU_SIZE + 1)
while read_pdu_size_cur == random_pdu_size:
	random_pdu_size = randrange(mb_util.MB_MIN_PDU_SIZE, mb_util.MB_MAX_PDU_SIZE + 1)
	
mb_bsp.write_mb_master_cs(mb_util.PDU_SIZE_REG, random_pdu_size)
read_pdu_size_cur = mb_bsp.read_mb_master_cs(mb_util.PDU_SIZE_REG)

if read_pdu_size_prv == read_pdu_size_cur:
	print('PDU size register test Successful')
else:
	print('PDU size register test Failed')
	error_count += 1
	print('read_pdu_size_prv = ', read_pdu_size_prv)
	print('read_pdu_size = ', read_pdu_size_cur)
print()


# Test configuration register
mismatch = 0
baud_rate_l = [i for i in range(4)]
conf_bit_l = [i << 8 for i in range(8)]
valid_config_value_l = list()
for baud_rate in baud_rate_l:
	for conf_bit in conf_bit_l:
		config_value = baud_rate + conf_bit
		valid_config_value_l.append(config_value)
		mb_bsp.write_mb_master_cs(mb_util.CONFIG_REG, config_value)
		read_config_value = mb_bsp.read_mb_master_cs(mb_util.CONFIG_REG)
		if read_config_value != config_value:
			print('PDU Configuration register test Failed')
			error_count += 1
			print('config_value = ', config_value)
			print('read_config_value = ', read_config_value)
			mismatch = 1

fake_config_value = randrange(0, 0xFFFFFFFF + 1)
while fake_config_value in valid_config_value_l:
	fake_config_value = randrange(0, 0xFFFFFFFF + 1)
	
mb_bsp.write_mb_master_cs(mb_util.CONFIG_REG, fake_config_value)
read_config_value = mb_bsp.read_mb_master_cs(mb_util.CONFIG_REG)
config_value = fake_config_value & ((0x7 << 8) | 0x3)
if read_config_value != config_value:
	print('PDU fake value Configuration register test Failed')
	error_count += 1
	print('config_value = ', config_value)
	print('fake_config_value = ', fake_config_value)
	print('read_config_value = ', read_config_value)	
	mismatch = 1	
	
if not mismatch:
	print('PDU Configuration register test Successful')
	
print()	
	
	
	
# Test Slave address register	
mismatch = 0
for i in range(mb_util.MB_MIN_SLAVE_ADDR, mb_util.MB_MAX_SLAVE_ADDR + 1):
	valid_slave_addr = i
	
	mb_bsp.write_mb_master_cs(mb_util.SLAVE_ADDR_REG, valid_slave_addr)

	read_slave_addr_cur = mb_bsp.read_mb_master_cs(mb_util.SLAVE_ADDR_REG)
	read_slave_addr_prv = read_slave_addr_cur

	if valid_slave_addr != read_slave_addr_cur:
		print('PDU slave address register test Failed')
		error_count += 1
		print('valid_slave_addr = ', valid_slave_addr)
		print('read_slave_addr_cur = ', read_slave_addr_cur)	
		mismatch = 1

if not mismatch:
	print('PDU slave address register test Successful')



fake_slave_addr = randrange(mb_util.MB_MAX_SLAVE_ADDR + 1, 0xFFFFFFFF + 1)

mb_bsp.write_mb_master_cs(mb_util.SLAVE_ADDR_REG, fake_slave_addr)

read_slave_addr_cur = mb_bsp.read_mb_master_cs(mb_util.SLAVE_ADDR_REG)

if read_slave_addr_prv == read_slave_addr_cur:
	print('PDU fake slave address register test Successful')
else:
	print('PDU fake slave address register test Failed')
	error_count += 1
	print('fake_slave_addr = ', fake_slave_addr)
	print('read_slave_addr_prv = ', read_slave_addr_prv)
	print('read_slave_addr_cur = ', read_slave_addr_cur)

print()	
	


print('Test Control and status interface for slave')
print()

# Test PDU size register
read_pdu_size_cur = mb_bsp.read_mb_slave_cs(mb_util.PDU_SIZE_REG)
read_pdu_size_prv = read_pdu_size_cur
random_pdu_size = randrange(mb_util.MB_MIN_PDU_SIZE, mb_util.MB_MAX_PDU_SIZE + 1)
while read_pdu_size_cur == random_pdu_size:
	random_pdu_size = randrange(mb_util.MB_MIN_PDU_SIZE, mb_util.MB_MAX_PDU_SIZE + 1)
	
mb_bsp.write_mb_slave_cs(mb_util.PDU_SIZE_REG, random_pdu_size)
read_pdu_size_cur = mb_bsp.read_mb_slave_cs(mb_util.PDU_SIZE_REG)

if read_pdu_size_prv == read_pdu_size_cur:
	print('PDU size register test Successful')
else:
	print('PDU size register test Failed')
	error_count += 1
	print('read_pdu_size_prv = ', read_pdu_size_prv)
	print('read_pdu_size = ', read_pdu_size_cur)
print()



# Test configuration register
mismatch = 0
baud_rate_l = [i for i in range(4)]
conf_bit_l = [i << 8 for i in range(8)]
valid_config_value_l = list()
for baud_rate in baud_rate_l:
	for conf_bit in conf_bit_l:
		config_value = baud_rate + conf_bit
		valid_config_value_l.append(config_value)
		mb_bsp.write_mb_slave_cs(mb_util.CONFIG_REG, config_value)
		read_config_value = mb_bsp.read_mb_slave_cs(mb_util.CONFIG_REG)
		if read_config_value != config_value:
			print('PDU Configuration register test Failed')
			error_count += 1
			print('config_value = ', config_value)
			print('read_config_value = ', read_config_value)
			mismatch = 1



fake_config_value = randrange(0, 0xFFFFFFFF + 1)
while fake_config_value in valid_config_value_l:
	fake_config_value = randrange(0, 0xFFFFFFFF + 1)
	
mb_bsp.write_mb_slave_cs(mb_util.CONFIG_REG, fake_config_value)
read_config_value = mb_bsp.read_mb_slave_cs(mb_util.CONFIG_REG)
config_value = fake_config_value & ((0x7 << 8) | 0x3)
if read_config_value != config_value:
	print('PDU fake value Configuration register test Failed')
	error_count += 1
	print('config_value = ', config_value)
	print('fake_config_value = ', fake_config_value)
	print('read_config_value = ', read_config_value)	
	mismatch = 1	
	
if not mismatch:
	print('PDU Configuration register test Successful')
	
print()	



# Test Slave address register	
mismatch = 0
for i in range(mb_util.MB_MIN_SLAVE_ADDR, mb_util.MB_MAX_SLAVE_ADDR + 1):
	valid_slave_addr = i
	
	mb_bsp.write_mb_slave_cs(mb_util.SLAVE_ADDR_REG, valid_slave_addr)

	read_slave_addr_cur = mb_bsp.read_mb_slave_cs(mb_util.SLAVE_ADDR_REG)
	read_slave_addr_prv = read_slave_addr_cur

	if valid_slave_addr != read_slave_addr_cur:
		print('PDU slave address register test Failed')
		error_count += 1
		print('valid_slave_addr = ', valid_slave_addr)
		print('read_slave_addr_cur = ', read_slave_addr_cur)	
		mismatch = 1

if not mismatch:
	print('PDU slave address register test Successful')



fake_slave_addr = randrange(mb_util.MB_MAX_SLAVE_ADDR + 1, 0xFFFFFFFF + 1)

mb_bsp.write_mb_slave_cs(mb_util.SLAVE_ADDR_REG, fake_slave_addr)

read_slave_addr_cur = mb_bsp.read_mb_slave_cs(mb_util.SLAVE_ADDR_REG)

if read_slave_addr_prv == read_slave_addr_cur:
	print('PDU fake slave address register test Successful')
else:
	print('PDU fake slave address register test Failed')
	error_count += 1
	print('fake_slave_addr = ', fake_slave_addr)
	print('read_slave_addr_prv = ', read_slave_addr_prv)
	print('read_slave_addr_cur = ', read_slave_addr_cur)


mb_util.print_test_result(error_count == 0)

