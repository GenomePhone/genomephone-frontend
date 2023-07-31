INSERT Project {
    name := <str>$name,
    ref := (INSERT Genome {
        data := <bytes>$reference_data
    }),
    targets := (
        WITH targets_data := <json>$targets,
        FOR target IN json_array_unpack(targets_data) UNION (INSERT Genome {
            data := <bytes>target
        })
    ),
    state := <ProjectState>"initialized",
};