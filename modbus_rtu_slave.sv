/*
	MIT License

	Copyright (c) 2021 Vasily Denisenko, Sergey Kuznetsov

	Permission is hereby granted, free of charge, to any person obtaining a copy
	of this software and associated documentation files (the "Software"), to deal
	in the Software without restriction, including without limitation the rights
	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
	copies of the Software, and to permit persons to whom the Software is
	furnished to do so, subject to the following conditions:

	The above copyright notice and this permission notice shall be included in all
	copies or substantial portions of the Software.

	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
	SOFTWARE.
*/



/*
	// Modbus Slave for RTU Transmission Mode      
    // For details, see README file.

	// Modules uart_transmitter and uart_receiver are taken from
	// https://github.com/roman-pogorelov/verlib/tree/master/ifaces/usart
    
	// Module modbus_crc16_calc is taken from
	// https://github.com/ItaruKawakomo/hdl
	
	// Other instances are taken from 
	// https://github.com/vasilydenisenko/hdl_primitives and
	// https://github.com/vasilydenisenko/fsm_kernels
	
    modbus_rtu_slave
	#(
		.BAUD_DIV_DEF 		( 3125 ),	 
		.BAUD_DIV_OPT1 		( 521 ),	
		.BAUD_DIV_OPT2 		( 20 ), 
		.CONFIG_DEFAULT 	( 2'h01 ),
		.ADDR_DEFAULT 		( 8'd1 ),
		.DE_TIME 			( 100 )
	)
		modbus_rtu_slave_inst
	(
		.clk 				(  ), // i
		.rst				(  ), // i
				
		.cs_addr 			(  ), // i[1:0]
		.cs_wr 				(  ), // i
		.cs_wrd 			(  ), // i[31:0]
		.cs_rdd 			(  ), // o[31:0]
				
		.pdu_addr 			(  ), // i[5:0]
		.pdu_wr 			(  ), // i
		.pdu_wrd 			(  ), // i[31:0]
		.pdu_rdd 			(  ), // o[31:0]
		
		.parity_err			(  ), // o
		.start_bit_err		(  ), // o
		.stop_bit_err		(  ), // o
		.addr_err			(  ), // o
		.crc_err			(  ), // o
		
		.control_pdu		(  ), // o
				
		.rxd 				(  ), // i
		.txd 				(  ), // o
		.oe  				(  )  // o
	); // modbus_rtu_slave_inst
*/



`default_nettype none
module modbus_rtu_slave
#(
	parameter BAUD_DIV_DEF = 2,	 
	parameter BAUD_DIV_OPT1 = 1,	 
	parameter BAUD_DIV_OPT2 = 1, 	
	parameter CONFIG_DEFAULT = 2'h01,
	parameter ADDR_DEFAULT = 8'd1,
	parameter DE_TIME = 100
)
(
	input  logic 			clk,
	input  logic 			rst,
	
	input  logic [1 : 0] 	cs_addr,
	input  logic 			cs_wr,
	input  logic [31 : 0]	cs_wrd,
	output logic [31 : 0]	cs_rdd,
	
	input  logic [5 : 0]	pdu_addr,
	input  logic 			pdu_wr,
	input  logic [31 : 0]	pdu_wrd,
	output logic [31 : 0]	pdu_rdd,
	
	output logic 			parity_err,
	output logic 			start_bit_err,
	output logic 			stop_bit_err,
	output logic 			addr_err,
	output logic 			crc_err,
	
	output logic 			control_pdu,
		
	input  logic 			rxd,
	output logic 			txd,
	output logic 			oe
);





// Timers
	localparam BAUD_DIV_9600 = BAUD_DIV_DEF << 1;
	localparam t15_BAUD_19200 = BAUD_DIV_DEF * 18 /*BAUD_DIV_DEF * CHAR_SIZE * 1.5*/;	// 18 = 12 bits/char * 1.5 char
	localparam t15_BAUD_9600 = t15_BAUD_19200 << 1;	// as a 9600 bps-period is twice of 19200 bps-period
	localparam t35_BAUD_19200 = BAUD_DIV_DEF * 42 /*BAUD_DIV_DEF * CHAR_SIZE * 3.5*/;	// 42 = 12 bits/char * 3.5 char
	localparam t35_BAUD_9600 = t35_BAUD_19200 << 1;	// as a 9600 bps-period is twice of 19200 bps-period

	localparam TIM_WIDTH = $clog2(t35_BAUD_9600 + 1); 	
	logic [TIM_WIDTH - 1 : 0] t15;
	assign t15 = (baud_code_reg == 2'd0) ? 
					t15_BAUD_9600[TIM_WIDTH - 1 : 0] :
					t15_BAUD_19200[TIM_WIDTH - 1 : 0];
	

	logic [TIM_WIDTH - 1 : 0] t35;
	assign t35 = (baud_code_reg == 2'd0) ? 
					t35_BAUD_9600[TIM_WIDTH - 1 : 0] :
					t35_BAUD_19200[TIM_WIDTH - 1 : 0];	
							
			
	logic silent_interval_ld;
	always_comb begin
		if (tx_done_st)
			silent_interval_ld = 1'b1;
		else if (rx_done_st)
			silent_interval_ld = 1'b1;
		else if (reception_st)
			silent_interval_ld = char_received;
		else
			silent_interval_ld = 1'b0;
	end
						
							
	logic silent_interval_ena;
	always_comb begin
		if (tx_wait_t35_st)
			silent_interval_ena = 1'b1;
		else if (reception_st)
			silent_interval_ena = 1'b1;
		else if (rx_wait_t35_st)
			silent_interval_ena = 1'b1;
		else 
			silent_interval_ena = 1'b0;
	end


	logic [TIM_WIDTH - 1 : 0] silent_interval_count;
	counter_up_dw_ld
	#(
		.DWIDTH 		(TIM_WIDTH),
		.DEFAULT_COUNT	(0)
	)
		silent_interval_timer_inst
	(
		.clk			(clk),
		.rst			(rst),		
		.cntrl__up_dwn	(1'b1),	// i
		.cntrl__load	(silent_interval_ld),	// i
		.cntrl__ena		(silent_interval_ena),	// i
		.cntrl__data_in	({TIM_WIDTH{1'b0}}),	// i[DWIDTH - 1 : 0]		
		.count			(silent_interval_count)	// o[DWIDTH - 1 : 0]
	);
	
	
	logic t15_expired;
	assign t15_expired = silent_interval_count == t15;


	logic t35_expired;
	assign t35_expired = silent_interval_count == t35;
//! Timers	



// RTU Receive FSM	
	logic reception_st;
	logic rx_wait_t35_st;
	logic rx_done_st;
	fsm_oe4s_sequencer              
		rtu_receive_fsm_inst
	(
		.clk	(clk),
		.rst	(rst),
		
		.t01	(char_received),	// i
		.t12	(t15_expired),	// i
		.t23	(t35_expired),	// i
		.t30	(1'b1),	// i
		
		.st0	(/*rx_idle_st*/),	// o
		.st1	(reception_st),	// o
		.st2	(rx_wait_t35_st),	// o
		.st3	(rx_done_st)	// o
	);
	
	
	logic control_frame;
	assign control_frame = reception_st && t15_expired;
		
	
	logic frame_received;
	srff_ar
	#(
		.POR_VALUE  (0)
	)
		frame_received_inst
	(
		.clk		(clk),
		.rst		(rst),		
		.s			(rx_done_st),	// i
		.r			(receive_st),	// i		
		.out		(frame_received)	// o
	);
//! RTU Receive FSM	



// RTU Transmit FSM
	logic emission_st;
	logic tx_wait_t35_st;
	logic tx_done_st;
	fsm_oe4s_sequencer
		rtu_transmit_fsm_inst
	(
		.clk	(clk),
		.rst	(rst),
		
		.t01	(emission_demand),	// i
		.t12	(frame_emitted),	// i
		.t23	(t35_expired),	// i
		.t30	(1'b1),	// i
		
		.st0	(/*tx_idle_st*/),	// o
		.st1	(emission_st),	// o
		.st2	(tx_wait_t35_st),	// o
		.st3	(tx_done_st)	// o
	);
	
	
	logic emission;				   			
	assign emission = emission_st; 
	
		
	logic frame_sent;
	assign frame_sent = tx_done_st;
//! RTU Transmit FSM




// Control and Status Interface
	localparam MAX_MODBUS_RTU_FRAME_SIZE = 256;
	localparam MIN_MODBUS_RTU_FRAME_SIZE = 4;
	
	localparam MAX_MODBUS_RTU_PDU_SIZE = 253;
	localparam MIN_MODBUS_RTU_PDU_SIZE = 1;
	
	localparam MIN_MODBUS_RTU_ADDR = 8'd1;
	localparam MAX_MODBUS_RTU_ADDR = 8'd247;
	
	
	// PDU size register
	logic pdu_size_wr;
	assign pdu_size_wr = cs_wr && (cs_addr == 2'd0);
	
	
	logic set_pdu_size;
	assign set_pdu_size =	pdu_size_wr && 
								(cs_wrd >= MIN_MODBUS_RTU_PDU_SIZE) &&
								(cs_wrd <= MAX_MODBUS_RTU_PDU_SIZE);

	
	
	logic [7 : 0] pdu_size;
	dff_ar
	#(
		.DWIDTH 	(8),
		.POR_VALUE 	(0)
	)
		pdu_size_inst
	(
		.clk		(clk),
		.rst		(rst),				
		.in			(cs_wrd[7 : 0]),	// i[DWIDTH - 1 : 0]
		.ena		(set_pdu_size),	// i
		.out		(pdu_size)	// o[DWIDTH - 1 : 0]
	);
	
	
	logic [8 : 0] transmit_frame_size;
	assign transmit_frame_size = pdu_size + 8'd3; // pdu_size + slave address (1 byte) + crc (2 bytes)

	
	logic [7 : 0] transmit_addr_pdu_size;
	assign transmit_addr_pdu_size = pdu_size + 8'd1; // pdu_size + slave address (1 byte)
	
	
	
	// Configuration register
	logic config_wr;
	assign config_wr = cs_wr && (cs_addr == 2'd1);
	
	
	logic [1 : 0] baud_code_reg;
	dff_ar
	#(
		.DWIDTH 	(2),		// Modbus RTU Transmission Mode Default:	
		.POR_VALUE 	(CONFIG_DEFAULT)		// Baud rate 19.2 kbps 
	)								
		baud_code_reg_inst
	(								
		.clk		(clk),
		.rst		(rst),		
		.in			(cs_wrd[1 : 0]),	// i[DWIDTH - 1 : 0]
		.ena		(config_wr),	// i
		.out		(baud_code_reg)	// o[DWIDTH - 1 : 0]
	);	
	
	
	logic [2 : 0] config_reg;
	dff_ar
	#(
		.DWIDTH 	(3),			// Modbus RTU Transmission Mode Defaults:
		.POR_VALUE 	(3'b0_0_1)		// [0] - Parity ena
	)								// [1] - Even (0)/Odd (1) parity
		config_reg_inst				// [2] - One (0)/Two (1) stop bit
	(								
		.clk		(clk),
		.rst		(rst),		
		.in			(cs_wrd[10 : 8]),	// i[DWIDTH - 1 : 0]
		.ena		(config_wr),	// i
		.out		(config_reg)	// o[DWIDTH - 1 : 0]
	);
	
		
	logic parity_ena;
	assign parity_ena = config_reg[0];	// 1'b0 - parity control disabled 
										// 1'b1 - parity control enabled		
	
	logic parity_type;
	assign parity_type = config_reg[1];		// 1'b0 - even
											// 1'b1 - odd		
	
	logic stop_bit_num;
	assign stop_bit_num = config_reg[2];	// 1'b0 - one stop bit 
											// 1'b1 - two stop bits
	

	
	
	// Slave address register
	logic slave_addr_wr;
	assign slave_addr_wr = cs_wr && (cs_addr == 2'd2);
	
	
	logic set_slave_addr;
	assign set_slave_addr = 	slave_addr_wr &&
								(cs_wrd >= MIN_MODBUS_RTU_ADDR) &&
								(cs_wrd <= MAX_MODBUS_RTU_ADDR);
								
	
	logic [7 : 0] slave_addr_reg;
	dff_ar
	#(
		.DWIDTH 	(8),			// Modbus RTU Transmission Mode Default:	
		.POR_VALUE 	(ADDR_DEFAULT)	// Baud rate 19.2 kbps 
	)								
		slave_addr_reg_inst
	(								
		.clk		(clk),
		.rst		(rst),		
		.in			(cs_wrd[7 : 0]),	// i[DWIDTH - 1 : 0]
		.ena		(set_slave_addr),	// i
		.out		(slave_addr_reg)	// o[DWIDTH - 1 : 0]
	);	
	
	assign addr_err = 	unicast_mode && 
						(slave_addr_reg != frame_byte[0]) && 
						control_frame;
	
	
	// Control and status register
	logic cntrl_stat_wr;
	assign cntrl_stat_wr = cs_wr && (cs_addr == 2'd3);
	
	
	logic process_end;
	assign process_end = cntrl_stat_wr;
								
								
	logic broadcast_mode;
	assign broadcast_mode = !unicast_mode;
	
	
	always_comb begin
		case (cs_addr)
			2'd0:		cs_rdd = {'0, received_pdu_size};	
			2'd1:		cs_rdd = {21'd0, config_reg, 6'd0, baud_code_reg};	
			2'd2:		cs_rdd = {'0, slave_addr_reg};	
			2'd3:		cs_rdd = {'0, unicast_mode, control_pdu};	
			default:	cs_rdd = 32'h0;	
		endcase
	end
//! Control and Status Interface	



// RTU Mode FSM	
	logic frame_error;
	srff_ar
	#(
		.POR_VALUE  (0)
	)
		frame_error_inst
	(
		.clk		(clk),
		.rst		(rst),		
		.s			(	parity_err || 
						start_bit_err || 
						stop_bit_err ||
						addr_err ||
						crc_err),	// i
		.r			(receive_start),	// i
		.out		(frame_error)	// o
	);
	

	logic receive_st;
	logic crc_calc_st;
	logic process_st;
	logic crc_gen_st;
	logic send_reply_st;	

	fsm_oe8s_universal
		rtu_slave_fsm_inst
	(
		.clk	( clk ),
		.rst	( rst ),
		
		.t0x	( control_frame ? 3'd1 : 3'd0 ),	// i[2 : 0]
		.t1x	( frame_error ? 3'd6 : 3'd2 ),	// i[2 : 0]
		.t2x	( end_crc_calc_st ? 3'd3 : 3'd2 ),	// i[2 : 0]
		.t3x	( frame_error ? 3'd6 : 3'd4 ),	// i[2 : 0]
		.t4x	( process_end ? 
						(unicast_mode ? 3'd5 : 3'd6 ) :
						3'd4 ),	// i[2 : 0]
		.t5x	( end_crc_gen_st ? 3'd6 : 3'd5 ),	// i[2 : 0]
		.t6x	( frame_received ?
						( (frame_error || broadcast_mode) ? 3'd0 : 3'd7) :
						3'd6 ),	// i[2 : 0]
		.t7x	( frame_sent ? 3'd0 : 3'd7 ),	// i[2 : 0]
		
		.st0	( receive_st ),	// o
		.st1	( /*check_addr_st*/ ),	// o
		.st2	( crc_calc_st ),	// o
		.st3	( /*check_crc_st*/ ),	// o
		.st4	( process_st ),	// o
		.st5	( crc_gen_st ),	// o
		.st6	( /*wait_frame_end_st*/ ),	// o
		.st7	( send_reply_st )	// o
	);

	
	
	
	assign control_pdu = process_st;
	
	
	logic emission_demand;
	assign emission_demand = send_reply_st;
	
	
	logic receive_start;
	edge_detector
		receive_st_detector_inst
	(
		.clk	(clk),
		.rst	(rst),
		
		.in		(receive_st), // i
		.rise	(receive_start), // o
		.fall	( ) // o
	);
//! RTU Mode FSM						
		




// Baud divisor selector
	localparam BDWIDTH = $clog2((BAUD_DIV_DEF << 1) + 1);	
	logic [BDWIDTH - 1 : 0] baud_divisor;
	always_comb begin
		case (baud_code_reg)
			2'd0: 		baud_divisor = BAUD_DIV_9600[BDWIDTH - 1 : 0];
			2'd1: 		baud_divisor = BAUD_DIV_DEF[BDWIDTH - 1 : 0];
			2'd2: 		baud_divisor = (BAUD_DIV_OPT1 < BAUD_DIV_DEF) ?
												BAUD_DIV_OPT1[BDWIDTH - 1 : 0] :
												BAUD_DIV_DEF[BDWIDTH - 1 : 0];
			2'd3: 		baud_divisor = (BAUD_DIV_OPT2 < BAUD_DIV_DEF) ?
												BAUD_DIV_OPT2[BDWIDTH - 1 : 0] :
												BAUD_DIV_DEF[BDWIDTH - 1 : 0];
			default: 	baud_divisor = BAUD_DIV_DEF[BDWIDTH - 1 : 0];
		endcase
	end
//! Baud divisor selector




// Driver Enable Timer
	logic det_ld;
	assign det_ld = transmit_end_st;
	
	
	logic det_ena;
	assign det_ena = transmit_start;

	
	localparam DET_WIDTH = $clog2(DE_TIME + 1);
	logic [DET_WIDTH - 1 : 0] de_count; 
	counter_up_dw_ld
	#(
		.DWIDTH 		(DET_WIDTH),
		.DEFAULT_COUNT	(0)
	)
		de_timer_inst
	(
		.clk			(clk),
		.rst			(rst),		
		.cntrl__up_dwn	(1'b1),	// i
		.cntrl__load	(det_ld),	// i
		.cntrl__ena		(det_ena),	// i
		.cntrl__data_in	({DET_WIDTH{1'b0}}),	// i[DWIDTH - 1 : 0]		
		.count			(de_count)	// o[DWIDTH - 1 : 0]
	);
	
	
	logic driver_enabled;
	assign driver_enabled = (de_count == DE_TIME);
//! Driver Enable Timer

		

// Transmit FSM	
	logic ptr_ld;
	assign ptr_ld = transmit_start || receive_start;
	
	
	logic ptr_ena;
	assign ptr_ena = char_transmit || char_received;
	

	logic [8 : 0] ptr; 
	counter_up_dw_ld
	#(
		.DWIDTH 		(9),
		.DEFAULT_COUNT	(0)
	)
		ptr_inst
	(
		.clk			(clk),
		.rst			(rst),		
		.cntrl__up_dwn	(1'b1),	// i
		.cntrl__load	(ptr_ld),	// i
		.cntrl__ena		(ptr_ena),	// i
		.cntrl__data_in	(9'd0),	// i[DWIDTH - 1 : 0]		
		.count			(ptr)	// o[DWIDTH - 1 : 0]
	);
	
	
	logic [8 : 0] received_addr_pdu_size_;
	assign received_addr_pdu_size_ = ptr - 2'd2;
	
	
	logic [7 : 0] received_addr_pdu_size;
	assign received_addr_pdu_size = received_addr_pdu_size_[7 : 0];
	
	
	logic [8 : 0] received_pdu_size;
	assign received_pdu_size = ptr - 2'd3;
	
	
	logic transmit_idle_st;
	logic transmit_st;
	logic transmit_end_st;
	fsm_oe4s_universal
		transmit_fsm_inst
	(
		.clk	(clk),
		.rst	(rst),
		
		.t0x	((emission && driver_enabled) ? 2'd1 : 2'd0),	// i[1 : 0]
		.t1x	(tx_ena ? 2'd2 : 2'd1),	// i[1 : 0]
		.t2x	((ptr < transmit_frame_size) ? 
								(2'd1) : 
								(tx_ena ? 2'd3 : 2'd2)),	// i[1 : 0]
		.t3x	(2'd0),	// i[1 : 0]
		
		.st0	(transmit_idle_st),	// o
		.st1	(transmit_st),	// o
		.st2	(/*next_byte_st*/),	// o
		.st3	(transmit_end_st)	// o
	);
	
	
	
	logic transmit_start;
	assign transmit_start = transmit_idle_st && emission;
	
	
	logic frame_emitted;
	assign frame_emitted = transmit_end_st;
//! Transmit FSM
		
		
		
// Transmitter	
	logic [7 : 0] tx_data;
	assign tx_data = frame_byte[ptr];
	
	
	logic tx_dav;
	assign tx_dav = transmit_st;
	
	
	logic tx_ena;
	uart_transmitter
	#(
		.BDWIDTH            (BDWIDTH)  // Разрядность делителя
	)
		uart_transmitter_inst
	(
		.reset              (rst), // i
		.clk                (clk), // i
		
		.ctrl_init          (1'b0), // i                    Инициализация (синхронный сброс)
		.ctrl_baud_divisor  (baud_divisor), // i  [BDWIDTH - 1 : 0] Значение делителя
		.ctrl_stop_bits     (stop_bit_num), // i                    Количество стоп-бит: 0 - один бит, 1 - два бита
		.ctrl_parity_ena    (parity_ena), // i                    Признак использования контроля паритета чет/нечет
		.ctrl_parity_type   (parity_type), // i                    Типа контроля паритета: 0 - чет, 1 - нечет
		
		.tx_data            (tx_data), // i  [7 : 0]
		.tx_valid           (tx_dav), // i
		.tx_ready           (tx_ena), // o
		
		.uart_txd           (txd)  // o
	);
	
	
	assign oe = emission;
	

	
	logic char_transmit;
	assign char_transmit = transmit_st && tx_ena;
//! Transmitter		



// Receiver	
	logic [7 : 0] rx_data;
	logic rx_dav;
	uart_receiver
	#(
		.BDWIDTH            (BDWIDTH)  // Разрядность делителя
	)
		uart_receiver_inst
	(
		.reset              (rst), // i
		.clk                (clk), // i

		.ctrl_init          (!receive_st), // i                    Инициализация (синхронный сброс)
		.ctrl_baud_divisor  (baud_divisor), // i  [BDWIDTH - 1 : 0] Значение делителя
		.ctrl_stop_bits     (stop_bit_num), // i                    Количество стоп-бит: 0 - один бит, 1 - два бита
		.ctrl_parity_ena    (parity_ena), // i                    Признак использования контроля паритета чет/нечет
		.ctrl_parity_type   (parity_type), // i                    Типа контроля паритета: 0 - чет, 1 - нечет

		.stat_err_parity    (parity_err), // o                    Признак ошибки паритета чет/нечет
		.stat_err_start     (start_bit_err), // o                    Признак ошибки приема старт-бита
		.stat_err_stop      (stop_bit_err), // o                    Признак ошибки приема стоп-бита

		.rx_data            (rx_data), // o  [7 : 0]
		.rx_valid           (rx_dav), // o

		.uart_rxd           (rxd)  // i
	);
	
	
	
	logic char_received;
	assign char_received = (receive_st && rx_dav);
//! Receiver	

		

		
// Frame Buffer	
	logic [MAX_MODBUS_RTU_FRAME_SIZE - 1 : 0][7 : 0] frame_byte_in;
	logic [MAX_MODBUS_RTU_FRAME_SIZE - 1 : 0] frame_byte_ena;
	logic [MAX_MODBUS_RTU_FRAME_SIZE - 1 : 0][7 : 0] frame_byte;


	assign frame_byte_in[0] = rx_data;							
	assign frame_byte_ena[0] = receive_st ? (rx_dav && (ptr == 0)) : 1'b0;	
	
	
	dff_ar
	#(
		.DWIDTH 	(8),
		.POR_VALUE 	(0)
	)
		frame_byte_0_reg_inst
	(
		.clk		(clk),
		.rst		(rst),				
		.in			(frame_byte_in[0]),	// i[DWIDTH - 1 : 0]
		.ena		(frame_byte_ena[0]),	// i
		.out		(frame_byte[0])	// o[DWIDTH - 1 : 0]
	);
	
	
	genvar i;
	generate
		for (i = 0; i < MAX_MODBUS_RTU_FRAME_SIZE - 1; i++) begin: frame_buf			
			always_comb begin
				if (receive_st)
					frame_byte_in[i + 1] = rx_data;
				else if (end_crc_gen_st)
					frame_byte_in[i + 1] = (i + 1 == pdu_size + 1) ? 
														crc_data[7 : 0] :
														crc_data[15 : 8];
				else
					frame_byte_in[i + 1] = pdu_wrd[8 * (i[1 : 0] + 1) - 1 : 8 * i[1 : 0]];
			end
			
			
			always_comb begin
				if (receive_st)
					frame_byte_ena[i + 1] = rx_dav && (ptr == i + 1);
				else if (end_crc_gen_st)
					frame_byte_ena[i + 1] = (i + 1 == pdu_size + 2) || 
											(i + 1 == pdu_size + 1);
				else
					frame_byte_ena[i + 1] = pdu_wr && (pdu_addr == (i >> 2));
			end

			
			dff_ar
			#(
				.DWIDTH 	(8),
				.POR_VALUE 	(0)
			)
				frame_byte_reg_inst
			(
				.clk		(clk),
				.rst		(rst),				
				.in			(frame_byte_in[i + 1]),	// i[DWIDTH - 1 : 0]
				.ena		(frame_byte_ena[i + 1]),	// i
				.out		(frame_byte[i + 1])	// o[DWIDTH - 1 : 0]
			);
		end: frame_buf
	endgenerate



	assign pdu_rdd = {	frame_byte[(pdu_addr << 2) + 4], 
						frame_byte[(pdu_addr << 2) + 3], 
						frame_byte[(pdu_addr << 2) + 2], 
						frame_byte[(pdu_addr << 2) + 1]};
						
						
	logic unicast_mode;
	assign unicast_mode = (frame_byte[0] != 8'd0);
//! Frame Buffer	




// CRC Engine
	logic start_crc_calc_st;
	logic end_crc_calc_st;
	fsm_oe4s_sequencer
		crc_calc_fsm_inst
	(
		.clk	( clk ),
		.rst	( rst ),
		
		.t01	( crc_calc_st ),	// i
		.t12	( 1'b1 ),	// i
		.t23	( crc_valid ),	// i
		.t30	( 1'b1 ),	// i
		
		.st0	(  ),	// o
		.st1	( start_crc_calc_st ),	// o
		.st2	(  ),	// o
		.st3	( end_crc_calc_st )	// o
	);


	logic start_crc_gen_st;
	logic end_crc_gen_st;
	fsm_oe4s_sequencer
		crc_gen_fsm_inst
	(
		.clk	( clk ),
		.rst	( rst ),
		
		.t01	( crc_gen_st ),	// i
		.t12	( 1'b1 ),	// i
		.t23	( crc_valid ),	// i
		.t30	( 1'b1 ),	// i
		
		.st0	(  ),	// o
		.st1	( start_crc_gen_st ),	// o
		.st2	(  ),	// o
		.st3	( end_crc_gen_st )	// o
	);


	logic crc_valid;
	logic [15 : 0] crc_data;
	modbus_crc16_calc
		modbus_crc16_calc_inst
	(
		.clk	    ( clk ),
		.reset	    ( rst ),
                               
	 	.data	    ( frame_byte ), // i      [256 -1 : 0][7 : 0]
                               
	 	.start  	( start_crc_calc_st || start_crc_gen_st ), // i
        .size 		( crc_calc_st ? 
							received_addr_pdu_size : 
							transmit_addr_pdu_size ), // i      [7 : 0]
    
        .crc_valid  ( crc_valid ), // o
        .crc_data   ( crc_data )  // o      [15 : 0]
	);
	
							
	logic crc_match;
	assign crc_match = crc_data == {frame_byte[ptr - 1], frame_byte[ptr - 2]};	
	
	
	assign crc_err = !crc_match && end_crc_calc_st;
//! CRC Engine



endmodule : modbus_rtu_slave