from strictyaml import Map, Regex, Seq, Str, Int, Optional, Seq, MapPattern, Enum, Bool

limits_schema = Map(
    {
        "time": Int(),
        Optional("memory", default=8192): Int(),
        Optional("output"): Int(),
        Optional("cores"): Str(),
    }
)

module_schema = Regex(r"\w+(\.\w+)*")

step_schema = Seq(Map({"step": module_schema}))

schema = Map(
    {
        "title": Str(),
        Optional("description"): Str(),
        "limits": limits_schema,
        "steps": Map({"run": step_schema, Optional("compile"): step_schema}),
        "tasks": MapPattern(
            Str(), Map({"type": Enum(["folder"]), Optional("path"): Str()})
        ),
        "tools": MapPattern(Str(), module_schema),
        "parameters": MapPattern(Str(), MapPattern(Str(), Str())),
    }
)
