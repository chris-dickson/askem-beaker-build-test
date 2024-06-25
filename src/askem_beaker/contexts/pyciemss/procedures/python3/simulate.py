# Define needed variables in above cell(s)
model # Selected model is loaded as a dictionary 

result = sample(
    model_path_or_json = model,
    start_time = {{ start_time | default("0.0")}},
    end_time = {{ end_time | default("90.0")}},
    logging_step_size = {{ logging_step_size | default("1.0")}},
    num_samples = {{ num_samples | default("100")}},
    alpha = {{ alpha | default("0.95")}},
    solver_method = '{{ solver_method | default("dopri5")}}',
    solver_options = {},
    noise_model = None,
    noise_model_kwargs = {},
    time_unit = None,
    static_state_interventions = {},
    static_parameter_interventions = {},
    dynamic_state_interventions = {},
    dynamic_parameter_interventions = {},
)