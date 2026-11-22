// tb_fir.v -- feeds input.mem through fir.v and checks every output
// against expected.txt (from Python's fir_fixed). Run from project root.
`timescale 1ns/1ps

module tb_fir;
    localparam N_SAMPLES = 1100;
    localparam OUT_W     = 19;

    reg                     clk = 0, rst = 1, in_valid = 0;
    reg  signed [15:0]      x_in = 0;
    wire                    out_valid;
    wire signed [OUT_W-1:0] y_out;

    fir dut (.clk(clk), .rst(rst), .in_valid(in_valid), .x_in(x_in),
             .out_valid(out_valid), .y_out(y_out));

    always #5 clk = ~clk;   // 100 MHz

    reg signed [15:0] x_mem [0:N_SAMPLES-1];
    integer expected [0:N_SAMPLES-1];
    integer fd, fout, n, r, errors, checked;

    initial begin
        $readmemh("vectors/input.mem", x_mem);
        fd = $fopen("vectors/expected.txt", "r");
        if (fd == 0) begin $display("Can't open expected.txt"); $finish; end
        for (n = 0; n < N_SAMPLES; n = n + 1)
            r = $fscanf(fd, "%d\n", expected[n]);
        $fclose(fd);

        // Creates file for hardware output comparisons with py
        fout = $fopen("vectors/actual.txt", "w");

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
            $fdisplay(fout, "%0d", y_out);
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