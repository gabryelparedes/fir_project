`timescale 1ns/1ps

module tb_fir;
    parameter N_SAMPLES = 1264;      // from params.txt
    parameter OUT_W     = 19;
    parameter ROUND     = 0;         // 0 = truncate, 1 = round half up
    parameter SAT = 0;               // 0 = wrap around, 1 = saturate

    reg                     clk = 0, rst = 1, in_valid = 0;
    reg  signed [15:0]      x_in = 0;
    wire                    out_valid;
    wire signed [OUT_W-1:0] y_out;

    // Setup filter
    fir #(.OUT_W(OUT_W), .ROUND(ROUND), .SAT(SAT)) dut (
        .clk(clk), .rst(rst), .in_valid(in_valid), .x_in(x_in),
        .out_valid(out_valid), .y_out(y_out));

    always #5 clk = ~clk;   // 100 MHz

    reg signed [15:0] x_mem [0:N_SAMPLES-1];
    integer expected [0:N_SAMPLES-1];
    integer fd, fout, n, r, errors, checked;
    reg [8*256-1:0] exp_file, act_file;     // file names (Verilog strings are bit vectors)

    initial begin
        if (!$value$plusargs("EXP=%s", exp_file)) exp_file = "vectors/expected.txt";
        if (!$value$plusargs("ACT=%s", act_file)) act_file = "vectors/actual.txt";

        $readmemh("vectors/input.mem", x_mem);
        fd = $fopen(exp_file, "r");
        if (fd == 0) begin $display("Can't open %0s", exp_file); $finish; end
        for (n = 0; n < N_SAMPLES; n = n + 1)
            r = $fscanf(fd, "%d\n", expected[n]);
        $fclose(fd);

        // Hardware outputs go here so Python can compare them 
        fout = $fopen(act_file, "w");

        $dumpfile("fir.vcd");
        $dumpvars(0, tb_fir);

        repeat (2) @(posedge clk);
        rst <= 0;

        // Drive one sample per clock
        for (n = 0; n < N_SAMPLES; n = n + 1) begin
            @(posedge clk);
            x_in     <= x_mem[n];
            in_valid <= 1;
        end
        @(posedge clk);
        in_valid <= 0;
        repeat (3) @(posedge clk);
        $fclose(fout);

        $write("[OUT_W=%0d ROUND=%0d SAT=%0d] ", OUT_W, ROUND, SAT);
        if (checked != N_SAMPLES)
            $display("FAIL: only checked %0d of %0d outputs", checked, N_SAMPLES);
        else if (errors == 0)
            $display("PASS: all %0d outputs match Python", checked);
        else
            $display("FAIL: %0d mismatches out of %0d", errors, checked);
        $finish;
    end

    // Checker: outputs come out in order, one per valid cycle
    initial begin errors = 0; checked = 0; end
    always @(posedge clk) begin
        if (out_valid) begin
            $fdisplay(fout, "%0d", y_out);   // signed decimal, one per line
            if (y_out !== expected[checked]) begin
                errors = errors + 1;
                if (errors <= 10)
                    $display("Mismatch at n=%0d: got %0d, expected %0d",
                             checked, y_out, expected[checked]);
            end
            checked = checked + 1;
        end
    end
endmodule
