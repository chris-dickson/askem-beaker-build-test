# Define needed variables in above cell(s)
model # Selected model is loaded as a dictionary 

result = optimize(
    model_path_or_json = model,

    # Interventions
    static_parameter_interventions = param_value_objective({{ param_names | default("[]") }}, [torch.tensor({{ start_time | default("0.0")}})]),
    objfun = lambda x: np.sum(np.abs(x)),
    initial_guess_interventions =  {{ initial_guess_interventions | default("[]")}},
    bounds_interventions = {{ bounds_interventions | default("[]")}},
    # in the empty array, add the state name with `_state` appended
    qoi = lambda samples: obs_nday_average_qoi(samples, [], 1),
    
    # Boundaries
    risk_bound = {{ risk_bound | default("300")}},
    start_time = {{ start_time | default("0.0")}},
    end_time = {{ end_time | default("90.0")}},
    
    # Additional Options
    alpha = {{ alpha | default("0.95")}},
    solver_method = '{{ solver_method | default("dopri5")}}',
    solver_options = {},
    n_samples_ouu = {{ n_samples_ouu | default("100")}},
    maxiter = {{ maxiter | default("5")}},
    maxfeval = {{ maxfeval | default("25")}},
    logging_step_size = {{ logging_step_size | default("1.0")}},
    verbose = False,
    roundup_decimal = 4,
)