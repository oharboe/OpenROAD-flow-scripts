// Blackbox stubs for fakeram modules used by macros.v
// The actual implementations come from ADDITIONAL_LEFS/ADDITIONAL_LIBS
(* blackbox *)
module fakeram7_2048x39(rd_out, addr_in, we_in, wd_in, clk, ce_in);
  output [38:0] rd_out;
  input  [10:0] addr_in;
  input         we_in;
  input  [38:0] wd_in;
  input         clk;
  input         ce_in;
endmodule

(* blackbox *)
module fakeram7_256x34(rd_out, addr_in, we_in, wd_in, clk, ce_in);
  output [33:0] rd_out;
  input  [7:0]  addr_in;
  input         we_in;
  input  [33:0] wd_in;
  input         clk;
  input         ce_in;
endmodule

(* blackbox *)
module fakeram7_64x21(rd_out, addr_in, we_in, wd_in, clk, ce_in);
  output [20:0] rd_out;
  input  [5:0]  addr_in;
  input         we_in;
  input  [20:0] wd_in;
  input         clk;
  input         ce_in;
endmodule
