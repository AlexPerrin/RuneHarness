// Decompiles the functions containing each address argument into
// re/decomp/<entry>.c.  Usage: -postScript Decompile.java 0x76100c 0x51d0a4
//@category osrsrl
import java.io.File;
import java.io.PrintWriter;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;

public class Decompile extends GhidraScript {
    @Override
    protected void run() throws Exception {
        File outDir = new File(System.getProperty("user.dir"), "re/decomp");
        outDir.mkdirs();
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        for (String arg : getScriptArgs()) {
            Function f = getFunctionContaining(toAddr(Long.decode(arg)));
            if (f == null) { println("no function at " + arg); continue; }
            DecompileResults res = ifc.decompileFunction(f, 300, monitor);
            if (!res.decompileCompleted()) { println("failed " + arg + ": " + res.getErrorMessage()); continue; }
            File out = new File(outDir, f.getEntryPoint() + ".c");
            try (PrintWriter w = new PrintWriter(out)) { w.print(res.getDecompiledFunction().getC()); }
            println("wrote " + out);
        }
        ifc.dispose();
    }
}
