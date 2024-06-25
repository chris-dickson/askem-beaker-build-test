---
layout: default
title: pypackage
parent: Contexts
nav_order: 1
has_toc: true
---

# pypackage

This is a basic context that leverages pypackage to learn more about target Python libraries before generating code with them. It can be used for demonstration purposes or truly ad hoc activities. For example, if a user asks to plot a dataframe with `seaborn` this context will attempt to gather help manual information for `seaborn` and provide it to the LLM agent to use during code generation. It is not currently supported or integrated into Terarium.