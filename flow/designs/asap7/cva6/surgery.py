"""SYNTH_VERILOG_SURGERY for cva6: the I-cache RAMs behind the techno cut.

cva6's sram_cache puts its RAMs behind tc_sram_wrapper_cache_techno, the
techno cut a technology's SRAM goes behind, and upstream fills it with
pulp's generic tc_sram, a model with port arrays and a read latency that
no SRAM macro has. This keeps the wrapper's parameters and ports and puts
a single-port SRAM with byte enables behind it, one module per shape
cv32a65x uses, for AUTO_MEMORIES to make a macro of: the I-cache data,
64 x 256 (32 byte enables), and the tag, 64 x 25 (4 byte enables, the
last of them 1 bit, as tc_sram's). An elaboration-time $error stops any
other shape.

An SRAM is not tc_sram: tc_sram's read data follows the last read
address, through idle cycles and writes, and a single-port SRAM reads
the address it is given and holds while idle. cva6_icache uses read
data only in a cycle after a read, or after idle cycles with no write
since the read, so the two return the same data whenever it is used.

The module is recognised by its text, token for token, comments and
whitespace aside: anything else stops the build. Every other file is
copied unchanged.
"""

import argparse
import os
import re
import sys

TECHNO = "tc_sram_wrapper_cache_techno"

TECHNO_EXPECTED = "module tc_sram_wrapper_cache_techno #( parameter int unsigned NumWords = 32'd1024, parameter int unsigned DataWidth = 32'd128, parameter int unsigned ByteWidth = 32'd8, parameter int unsigned NumPorts = 32'd2, parameter int unsigned Latency = 32'd1, parameter SimInit = \"none\", parameter BYTE_ACCESS = 1, parameter bit PrintSimCfg = 1'b0, parameter int unsigned AddrWidth = (NumWords > 32'd1) ? $clog2(NumWords) : 32'd1, parameter int unsigned BeWidth = (DataWidth + ByteWidth - 32'd1) / ByteWidth, parameter type addr_t = logic [AddrWidth-1:0], parameter type data_t = logic [DataWidth-1:0], parameter type be_t = logic [BeWidth-1:0] ) ( input logic clk_i, input logic rst_ni, input logic [NumPorts-1:0] req_i, input logic [NumPorts-1:0] we_i, input addr_t [NumPorts-1:0] addr_i, input data_t [NumPorts-1:0] wdata_i, input be_t [NumPorts-1:0] be_i, output data_t [NumPorts-1:0] rdata_o ); tc_sram #( .NumWords(NumWords), .DataWidth(DataWidth), .ByteWidth(ByteWidth), .NumPorts(NumPorts), .Latency(Latency), .SimInit(SimInit), .PrintSimCfg(PrintSimCfg) ) i_tc_sram ( .clk_i ( clk_i ), .rst_ni ( rst_ni ), .req_i ( req_i ), .we_i ( we_i ), .be_i ( be_i ), .wdata_i ( wdata_i ), .addr_i ( addr_i ), .rdata_o ( rdata_o ) ); endmodule"

TECHNO_REPLACEMENT = """module tc_sram_wrapper_cache_techno #(
  parameter int unsigned NumWords     = 32'd1024, // Number of Words in data array
  parameter int unsigned DataWidth    = 32'd128,  // Data signal width
  parameter int unsigned ByteWidth    = 32'd8,    // Width of a data byte
  parameter int unsigned NumPorts     = 32'd2,    // Number of read and write ports
  parameter int unsigned Latency      = 32'd1,    // Latency when the read data is available
  parameter              SimInit      = "none",   // Simulation initialization
  parameter              BYTE_ACCESS  = 1,
  parameter bit          PrintSimCfg  = 1'b0,     // Print configuration
  parameter int unsigned AddrWidth = (NumWords > 32'd1) ? $clog2(NumWords) : 32'd1,
  parameter int unsigned BeWidth   = (DataWidth + ByteWidth - 32'd1) / ByteWidth, // ceil_div
  parameter type         addr_t    = logic [AddrWidth-1:0],
  parameter type         data_t    = logic [DataWidth-1:0],
  parameter type         be_t      = logic [BeWidth-1:0]
) (
  input  logic                 clk_i,
  input  logic                 rst_ni,
  input  logic  [NumPorts-1:0] req_i,
  input  logic  [NumPorts-1:0] we_i,
  input  addr_t [NumPorts-1:0] addr_i,
  input  data_t [NumPorts-1:0] wdata_i,
  input  be_t   [NumPorts-1:0] be_i,
  output data_t [NumPorts-1:0] rdata_o
);
  // SYNTH_VERILOG_SURGERY (asap7/cva6/surgery.py): a single-port SRAM with
  // byte enables behind the techno cut, for the shapes cv32a65x uses.
  if (NumPorts != 1 || Latency != 1 || ByteWidth != 8 || NumWords != 64
      || !(DataWidth == 256 || DataWidth == 25)) begin : gen_surgery_shape
    $error("cva6 surgery: tc_sram_wrapper_cache_techno rewritten for 1 port, latency 1, 64 words of 256 or 25 bits");
  end
  if (DataWidth == 256) begin : gen_data
    cva6_icache_data_sram i_sram (
        .clk(clk_i), .cs(req_i[0]), .we(we_i[0]), .addr(addr_i[0]),
        .wdata(wdata_i[0]), .be(be_i[0]), .rdata(rdata_o[0]));
  end else begin : gen_tag
    cva6_icache_tag_sram i_sram (
        .clk(clk_i), .cs(req_i[0]), .we(we_i[0]), .addr(addr_i[0]),
        .wdata(wdata_i[0]), .be(be_i[0]), .rdata(rdata_o[0]));
  end
endmodule

// The I-cache data RAM, behavioural; AUTO_MEMORIES makes it a macro.
// WORDS is 64 where the techno cut instances it; a check may shrink it.
module cva6_icache_data_sram #(
    parameter WORDS = 64,
    parameter AW    = $clog2(WORDS)
) (
    input               clk,
    input               cs,
    input               we,
    input      [AW-1:0] addr,
    input      [255:0]  wdata,
    input      [31:0]   be,
    output reg [255:0]  rdata
);
  reg [255:0] mem [0:WORDS-1];
  integer j;
  always @(posedge clk)
    if (cs) begin
      if (we)
        for (j = 0; j < 32; j = j + 1)
          if (be[j]) mem[addr][j*8 +: 8] <= wdata[j*8 +: 8];
      rdata <= mem[addr];
    end
endmodule

// The I-cache tag RAM, behavioural; AUTO_MEMORIES makes it a macro. Its
// last byte enable covers the one bit left over, as tc_sram's does.
module cva6_icache_tag_sram #(
    parameter WORDS = 64,
    parameter AW    = $clog2(WORDS)
) (
    input               clk,
    input               cs,
    input               we,
    input      [AW-1:0] addr,
    input      [24:0]   wdata,
    input      [3:0]    be,
    output reg [24:0]   rdata
);
  reg [24:0] mem [0:WORDS-1];
  always @(posedge clk)
    if (cs) begin
      if (we) begin
        if (be[0]) mem[addr][7:0]   <= wdata[7:0];
        if (be[1]) mem[addr][15:8]  <= wdata[15:8];
        if (be[2]) mem[addr][23:16] <= wdata[23:16];
        if (be[3]) mem[addr][24]    <= wdata[24];
      end
      rdata <= mem[addr];
    end
endmodule"""


def norm(text):
    text = re.sub(r"//[^\n]*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return " ".join(text.split())


def fail(msg):
    sys.exit("cva6 surgery: " + msg)


def rewrite(path, text, module, expected, replacement):
    """`text` with `module` rewritten, and the number of rewrites"""
    found = list(
        re.finditer(r"^module\s+%s\b.*?^endmodule\b" % module, text, re.M | re.S)
    )
    if len(found) > 1:
        fail("%s defines %s %d times" % (path, module, len(found)))
    if not found:
        return text, 0
    m = found[0]
    if norm(m.group(0)) != expected:
        fail("%s in %s is not the %s this rewrite knows" % (module, path, module))
    return text[: m.start()] + replacement + text[m.end() :], 1


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out-dir", required=True)
    p.add_argument("files", nargs="+")
    a = p.parse_args()
    rewrites = [[TECHNO, TECHNO_EXPECTED, TECHNO_REPLACEMENT, 0]]
    for path in a.files:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        for r in rewrites:
            text, n = rewrite(path, text, r[0], r[1], r[2])
            r[3] += n
        with open(
            os.path.join(a.out_dir, os.path.basename(path)), "w", encoding="utf-8"
        ) as f:
            f.write(text)
    for module, _, _, done in rewrites:
        if done != 1:
            fail("%s found in %d files, not one" % (module, done))


if __name__ == "__main__":
    main()
