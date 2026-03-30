// Blackbox stubs for fakeram modules used by tinyRocket
(* blackbox *)
module fakeram45_64x32(rd_out, addr_in, we_in, w_mask_in, wd_in, clk, ce_in);
  output [31:0] rd_out;
  input  [5:0]  addr_in;
  input         we_in;
  input  [31:0] w_mask_in;
  input  [31:0] wd_in;
  input         clk;
  input         ce_in;
endmodule

(* blackbox *)
module fakeram45_1024x32(rd_out, addr_in, we_in, w_mask_in, wd_in, clk, ce_in);
  output [31:0] rd_out;
  input  [9:0]  addr_in;
  input         we_in;
  input  [31:0] w_mask_in;
  input  [31:0] wd_in;
  input         clk;
  input         ce_in;
endmodule
