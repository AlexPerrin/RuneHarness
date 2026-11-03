// Lists functions with an instruction whose operand is one of the given scalars
// (e.g. struct field offsets). Usage: -postScript FindScalar.java 0x89494 0x89498
//@category osrsrl
import java.util.*;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.scalar.Scalar;

public class FindScalar extends GhidraScript {
    @Override
    protected void run() throws Exception {
        Set<Long> wanted = new HashSet<>();
        for (String a : getScriptArgs()) wanted.add(Long.decode(a));
        Map<String, Set<Long>> byFunction = new TreeMap<>();
        InstructionIterator it = currentProgram.getListing().getInstructions(true);
        while (it.hasNext() && !monitor.isCancelled()) {
            Instruction ins = it.next();
            for (int i = 0; i < ins.getNumOperands(); i++) {
                for (Object o : ins.getOpObjects(i)) {
                    if (o instanceof Scalar && wanted.contains(((Scalar) o).getUnsignedValue())) {
                        Function f = getFunctionContaining(ins.getAddress());
                        String key = f == null ? "<none>@" + ins.getAddress() : f.getName() + "@" + f.getEntryPoint() + " (" + f.getBody().getNumAddresses() + " bytes)";
                        byFunction.computeIfAbsent(key, k -> new TreeSet<>()).add(((Scalar) o).getUnsignedValue());
                    }
                }
            }
        }
        for (Map.Entry<String, Set<Long>> e : byFunction.entrySet()) {
            StringBuilder sb = new StringBuilder();
            for (long v : e.getValue()) sb.append(" 0x").append(Long.toHexString(v));
            println("SCALAR " + e.getKey() + ":" + sb);
        }
    }
}
