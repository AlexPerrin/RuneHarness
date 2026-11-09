// Prints the functions calling each address argument (Ghidra addresses), one line per caller with its call
// sites, then a count of non-call references (data/pointer refs hint at indirect calls).
// Usage: -postScript Callers.java 0x5320dc 0x632748
// Output:
//   CALLERS 0x5320dc FUN_005320dc: 3 callers, 5 sites, 0 other refs
//     FUN_00512e78@00512e78 005147d8
//     <no function> 005193d8        (a call site Ghidra hasn't placed in a function)
// Covers what Ghidra has disassembled only; cross-check with objdump (see .claude/skills/reverse/SKILL.md).
//@category osrsrl
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;

public class Callers extends GhidraScript {
    @Override
    protected void run() throws Exception {
        for (String arg : getScriptArgs()) {
            Address target = toAddr(Long.decode(arg));
            Function callee = getFunctionAt(target);
            Map<String, List<String>> byCaller = new TreeMap<>();
            int sites = 0, other = 0;
            for (Reference r : getReferencesTo(target)) {
                if (!r.getReferenceType().isCall()) { other++; continue; }
                Function f = getFunctionContaining(r.getFromAddress());
                String key = f == null ? "<no function>" : f.getName() + "@" + f.getEntryPoint();
                byCaller.computeIfAbsent(key, k -> new ArrayList<>()).add(r.getFromAddress().toString());
                sites++;
            }
            int callers = byCaller.size() - (byCaller.containsKey("<no function>") ? 1 : 0);
            println(String.format("CALLERS %s %s: %d callers, %d sites, %d other refs", arg,
                    callee == null ? "<not a function entry>" : callee.getName(), callers, sites, other));
            for (Map.Entry<String, List<String>> e : byCaller.entrySet()) {
                List<String> s = e.getValue();
                s.sort(null);
                println("    " + e.getKey() + " " + String.join(" ", s));
            }
        }
    }
}
