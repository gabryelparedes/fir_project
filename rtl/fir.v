// fir.v -- 41-tap direct-form FIR, one sample per clock
//
// Math (matches fir_fixed() in Python, bit for bit):
//   acc[n] = sum_{k=0}^{N-1} coef[k] * x[n-k]      (full precision)
//   y[n]   = (acc[n] + half) >>> F                 (half = 2^(F-1) if ROUND, else 0)
//   then fit y[n] into OUT_W bits: wrap around, or clamp if SAT
//
// Widths:
//   x      : B_X-bit signed, Q1.15  (value = x_int / 2^15)
//   coef   : B_COEF-bit signed, scaled by 2^F
//   acc    : needs 34 bits worst case (2^15 * sum|coef| < 2^33) -> 36 for margin
//   y_out  : default ACC_W - F = 19 bits, which can't overflow.
//            Set OUT_W = 16 to keep the output the same size as the input;
//            then the ~1.6x worst-case gain CAN overflow, and SAT decides what happens.
//
// Timing: y_out for sample x[n] appears one clock after x[n] is presented
// with in_valid high.

module fir #(
    parameter N         = 41,
    parameter B_X       = 16,
    parameter B_COEF    = 16,
    parameter F         = 17,              // from params.txt
    parameter ACC_W     = 36,
    parameter OUT_W     = ACC_W - F,       // must be <= ACC_W - F
    parameter ROUND     = 0,               // 0 = truncate, 1 = round half up
    parameter SAT       = 0,               // 0 = wrap around, 1 = saturate
    parameter COEF_FILE = "vectors/coeffs.mem"
)(
    input  wire                     clk,
    input  wire                     rst,       // synchronous, active high
    input  wire                     in_valid,
    input  wire signed [B_X-1:0]    x_in,
    output reg                      out_valid,
    output reg  signed [OUT_W-1:0]  y_out
);

    localparam SH_W = ACC_W - F;           // width left after the shift (19)

    // Coefficient ROM, loaded from Python's export
    reg signed [B_COEF-1:0] coef [0:N-1];
    initial $readmemh(COEF_FILE, coef);

    // Delay line: dly[0] = x[n-1], dly[1] = x[n-2], ..., dly[N-2] = x[n-N+1]
    reg signed [B_X-1:0] dly [0:N-2];

    // Multiply-accumulate (combinational)
    // Every operand is signed and the result is ACC_W bits wide, so Verilog
    // sign-extends each product to ACC_W bits before adding.
    integer k;
    reg signed [ACC_W-1:0] acc;
    always @* begin
        acc = x_in * coef[0];                       // k = 0 term uses x[n] itself
        for (k = 1; k < N; k = k + 1)
            acc = acc + dly[k-1] * coef[k];
    end

    // ---- Rounding --------------------------------------------------------
    // Shifting right by F rounds DOWN (toward -infinity). Adding half of the
    // amount being shifted off first turns that into round-to-nearest.
    localparam [ACC_W-1:0] HALF = ROUND ? ({{(ACC_W-1){1'b0}}, 1'b1} << (F-1))
                                        : {ACC_W{1'b0}};
    wire signed [ACC_W-1:0] acc_r = acc + $signed(HALF);
    wire signed [SH_W-1:0]  sh    = acc_r >>> F;   // upper bits are just sign copies

    // ---- Fit into OUT_W bits ---------------------------------------------
    // sh fits in OUT_W bits exactly when its top (SH_W - OUT_W + 1) bits are
    // all 0s (small positive) or all 1s (small negative). Otherwise it overflowed.
    wire [SH_W-OUT_W:0] top  = sh[SH_W-1:OUT_W-1];
    wire                fits = (&top) | ~(|top);

    localparam signed [OUT_W-1:0] MAX_OUT = {1'b0, {(OUT_W-1){1'b1}}};  // 0111...1
    localparam signed [OUT_W-1:0] MIN_OUT = {1'b1, {(OUT_W-1){1'b0}}};  // 1000...0

    wire signed [OUT_W-1:0] y_next =
        (!SAT || fits) ? sh[OUT_W-1:0]                 // wrap: keep the low bits
                       : (sh[SH_W-1] ? MIN_OUT : MAX_OUT);  // clamp, by sign

    // Register output, shift delay line
    integer i;
    always @(posedge clk) begin
        if (rst) begin
            out_valid <= 1'b0;
            y_out     <= {OUT_W{1'b0}};
            for (i = 0; i < N-1; i = i + 1)
                dly[i] <= {B_X{1'b0}};
        end else begin
            out_valid <= in_valid;
            if (in_valid) begin
                y_out  <= y_next;
                dly[0] <= x_in;
                for (i = 1; i < N-1; i = i + 1)
                    dly[i] <= dly[i-1];
            end
        end
    end

endmodule
