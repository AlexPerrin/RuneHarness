// Prints the functions referencing each address argument (Ghidra addresses).
// Usage: -postScript Xrefs.java 0xb82958 0x19d1a50
//@category osrsrl
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;

public class Xrefs extends GhidraScript {
    @Override
    protected void run() throws Exception {
        for (String arg : getScriptArgs()) {
            println("REFS " + arg);
            for (Reference r : getReferencesTo(toAddr(Long.decode(arg)))) {
                Function f = getFunctionContaining(r.getFromAddress());
                println(String.format("    from %s %s in %s", r.getFromAddress(), r.getReferenceType(),
                        f == null ? "<no function>"
                                : f.getName() + "@" + f.getEntryPoint() + " (" + f.getBody().getNumAddresses() + " bytes)"));
            }
        }
    }
}
