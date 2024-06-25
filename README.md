# ASKEM Beaker: integrated AI-enabled coding notebooks within Terarium

This repo uses Jataware's [Beaker-Kernel](https://github.com/jataware/beaker-kernel) to provide customized contexts for dataset manipulation, model editing and configuration and other core operations within Terarium, thereby enabling Terarium to have an embedded notebook with seameless HMI integration.

In addition to an integrated notebook/coding environment for the scientific workflow, ASKEM Beaker offers an AI assistant that can support scientitific tasks such as model stratification, regridding, etc. The AI assistant is powered by Jataware's [Archytas](https://github.com/jataware/archytas) framework, a custom implementation of the [ReAct framework](https://react-lm.github.io/). The AI assistant has contextual awareness of code creation and execution in the notebook and can support the Terarium user in generating code for difficult operations in the ASKEM frameworks (e.g. Mira, Decapodes, etc).

To learn more about Beaker for Terarium we encourage developers and users to check out our [comprehensive documentation](https://darpa-askem.github.io/askem-beaker/).

## Quickstart

Run `make .env` which will copy the `env.example` to `.env`. Make sure to update `.env` and to set your `OPENAI_API_KEY` in your environment (e.g. `export OPENAI_API_KEY=your_key_here`). Next, run `make build`.

Now you're ready to run the stack with `make dev` which will run the development stack inside `docker-compose`.

> **Note**: the developer stack is currently in a transition from `TDS` to `HMI-Server` and the `docker-compose.yaml` needs to be updated accordingly. As a workaround, you can set `.env`'s `HMI-Server` settings to point to a remote instance of `HMI-Server` (e.g. `staging`) and use the `docker-compose-remote` setup with `docker-compose -f docker-compose-remote.yaml up`.

## Contexts

Please refer to the [full documentation](https://darpa-askem.github.io/askem-beaker/) for `askem-beaker` to learn more about each supported context and how to leverage it.
