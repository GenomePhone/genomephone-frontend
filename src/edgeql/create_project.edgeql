INSERT Project {
    name := <str>$name,
    ref := assert_single((SELECT Reference FILTER .name = $reference_name)),
    targets := (
        WITH targets_data := <json>$targets,
        FOR target IN json_array_unpack(targets_data) UNION (INSERT Genome {
            data := <bytes>target
        })
    ),
    state := <ProjectState>"initialized",
};