// For each string literal containing one of the script arguments, prints the
// functions that reference it.  Usage (headless):
//   -postScript StringXrefs.java "Walk here" "~debugproc" ...
//@category osrsrl
import ghidra.app.script.GhidraScript;
import ghidra.program.model.data.StringDataInstance;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.DataIterator;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;

public class StringXrefs extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] needles = getScriptArgs();
        DataIterator it = currentProgram.getListing().getDefinedData(true);
        while (it.hasNext() && !monitor.isCancelled()) {
            Data d = it.next();
            if (!StringDataInstance.isString(d)) continue;
            String s = StringDataInstance.getStringDataInstance(d).getStringValue();
            if (s == null) continue;
            for (String n : needles) {
                if (!s.contains(n)) continue;
                String shown = s.length() > 90 ? s.substring(0, 90) + "..." : s;
                println(String.format("STR %s \"%s\"", d.getAddress(), shown.replace("\n", "\\n")));
                for (Reference r : getReferencesTo(d.getAddress())) {
                    Function f = getFunctionContaining(r.getFromAddress());
                    println(String.format("    from %s in %s", r.getFromAddress(),
                            f == null ? "<no function>" : f.getName() + "@" + f.getEntryPoint()
                                    + " (" + f.getBody().getNumAddresses() + " bytes)"));
                }
                break;
            }
        }
    }
}
