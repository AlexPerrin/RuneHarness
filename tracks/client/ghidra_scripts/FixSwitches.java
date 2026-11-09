// Completes switch tables auto-analysis left unresolved or partial (AArch64 `ldrh` + `adr` + `br` tables): for
// every function with a `br`, decompile it and, for each jump table the decompiler recovers, add the missing
// COMPUTED_JUMP refs, disassemble the cases and fix up the function body. Repeats until a pass adds nothing.
// Writes the project (run without -readOnly, one writer at a time); arg "dry" only reports.
// Usage: -postScript FixSwitches.java   (after auto-analysis; then one more auto-analysis pass)
//@category osrsrl
import java.util.*;

import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.cmd.function.CreateFunctionCmd;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileOptions;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.listing.*;
import ghidra.program.model.pcode.HighFunction;
import ghidra.program.model.pcode.JumpTable;
import ghidra.program.model.symbol.*;

public class FixSwitches extends GhidraScript {
    @Override
    protected void run() throws Exception {
        boolean dry = getScriptArgs().length > 0 && getScriptArgs()[0].equals("dry");
        DecompInterface ifc = new DecompInterface();
        DecompileOptions opts = new DecompileOptions();
        opts.grabFromProgram(currentProgram);
        ifc.setOptions(opts);
        ifc.openProgram(currentProgram);
        Listing l = currentProgram.getListing();
        ReferenceManager rm = currentProgram.getReferenceManager();
        Set<Address> failed = new HashSet<>();
        for (int pass = 1; pass <= 10; pass++) {
            Map<Function, List<Address>> todo = new LinkedHashMap<>();
            for (Instruction ins : l.getInstructions(true)) {
                FlowType ft = ins.getFlowType();
                if (!ft.isJump() || !ft.isComputed() || ft.isCall() || failed.contains(ins.getAddress())) continue;
                if (!"br".equals(ins.getMnemonicString())) continue;
                Function f = getFunctionContaining(ins.getAddress());
                if (f == null) continue;
                todo.computeIfAbsent(f, k -> new ArrayList<>()).add(ins.getAddress());
            }
            int tables = 0, cases = 0;
            for (Map.Entry<Function, List<Address>> e : todo.entrySet()) {
                if (monitor.isCancelled()) return;
                Function f = e.getKey();
                DecompileResults res = ifc.decompileFunction(f, 300, monitor);
                HighFunction hf = res.getHighFunction();
                Set<Address> fixed = new HashSet<>();
                int tablesBefore = tables;
                if (hf != null) {
                    for (JumpTable jt : hf.getJumpTables()) {
                        Address sw = jt.getSwitchAddress();
                        if (!e.getValue().contains(sw)) continue;
                        Address[] dests = jt.getCases();
                        fixed.add(sw);
                        Set<Address> have = new HashSet<>();
                        for (Reference r : rm.getReferencesFrom(sw)) if (r.getReferenceType().isFlow()) have.add(r.getToAddress());
                        List<Address> missing = new ArrayList<>();
                        for (Address d : dests) if (!have.contains(d)) missing.add(d);
                        if (missing.isEmpty()) continue;
                        dests = missing.toArray(new Address[0]);
                        tables++; cases += dests.length;
                        if (dry) { println("TABLE " + f.getName() + " " + sw + " cases " + dests.length); continue; }
                        AddressSet starts = new AddressSet();
                        for (Address d : dests) {
                            rm.addMemoryReference(sw, d, RefType.COMPUTED_JUMP, SourceType.ANALYSIS, CodeUnit.MNEMONIC);
                            if (l.getInstructionAt(d) == null) starts.add(d);
                        }
                        if (!starts.isEmpty()) new DisassembleCommand(starts, null, true).applyTo(currentProgram, monitor);
                    }
                }
                for (Address a : e.getValue()) failed.add(a);
                if (!dry && tablesBefore != tables) CreateFunctionCmd.fixupFunctionBody(currentProgram, f, monitor);
            }
            println("PASS " + pass + " functions " + todo.size() + " tables " + tables + " cases " + cases
                    + " brs seen " + failed.size());
            if (dry || tables == 0) break;
        }
        ifc.dispose();
    }
}
