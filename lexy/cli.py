import os
import shutil

import click
from dotenv import dotenv_values, set_key


@click.group()
@click.option('--debug', is_flag=True, help='Debug mode')
@click.pass_context
def cli(ctx, debug):
    ctx.ensure_object(dict)
    ctx.obj['debug'] = debug


@cli.command(help="Initialize Lexy")
@click.option('--project-dir',
              default='.',
              help='Project home directory',
              show_default=True,
              type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True, resolve_path=True))
@click.option('--pipeline-dir',
              default='./pipelines',
              help='Directory to store Lexy pipelines',
              show_default=True,
              type=click.Path(exists=False, file_okay=False, dir_okay=True, writable=True, resolve_path=True))
@click.option('--overwrite', is_flag=True, help='Overwrite existing values')
@click.option('--no-input', is_flag=True, help='Do not prompt for input')
@click.pass_context
def init(ctx, project_dir, pipeline_dir, overwrite, no_input):

    if ctx.obj['debug']:
        click.echo(f"Debug mode: {ctx.obj['debug']}")

    # Project directory
    default_project_dir = os.path.expanduser(project_dir)
    if not no_input:
        # Prompt user
        project_dir = click.prompt("Project directory", default=default_project_dir)
    else:
        # Use default values
        project_dir = default_project_dir
    # Check if the project directory exists
    if not os.path.exists(project_dir):
        click.secho(f"Directory does not exist: {project_dir}", err=True, fg="red")
        raise click.Abort()

    # Pipeline directory
    default_pipeline_dir = os.path.expanduser(pipeline_dir)
    if not no_input:
        # Prompt user
        pipeline_dir = click.prompt("Lexy pipeline directory", default=default_pipeline_dir)
    else:
        # Use default values
        pipeline_dir = default_pipeline_dir

    # Check if an .env file exists in the project directory
    env_file = os.path.join(project_dir, ".env")
    if not os.path.exists(env_file):
        # Copy the .env.example template to the current working directory
        env_example_file = os.path.join(os.path.dirname(__file__), "templates", ".env.example")
        shutil.copy(env_example_file, env_file)
        click.secho(f"Copied .env.example to {env_file}", fg="blue")
    else:
        click.secho(f"Found existing .env file: {env_file}", fg="blue")

    # Load the .env file
    dotenv_config = dotenv_values(env_file)
    if ctx.obj['debug']:
        click.secho(f"Loaded .env file: {env_file}", fg="blue")

    # Check if PIPELINE_DIR is already set in the .env file
    if "PIPELINE_DIR" in dotenv_config and dotenv_config["PIPELINE_DIR"] == pipeline_dir:
        click.secho(f"PIPELINE_DIR already set: {pipeline_dir}", fg="blue")
    elif "PIPELINE_DIR" in dotenv_config and dotenv_config["PIPELINE_DIR"] != pipeline_dir:
        click.secho(f"PIPELINE_DIR already set: {dotenv_config['PIPELINE_DIR']}", err=True, fg="yellow")
        if not no_input:
            click.confirm("Do you want to overwrite the existing value?", abort=True)
            set_key(env_file, "PIPELINE_DIR", pipeline_dir)
            click.secho(f"Set PIPELINE_DIR in .env file: {pipeline_dir}", fg="blue")
        else:
            if overwrite:
                set_key(env_file, "PIPELINE_DIR", pipeline_dir)
                click.secho(f"Set PIPELINE_DIR in .env file: {pipeline_dir}", fg="blue")
            else:
                click.secho(f"Existing value for PIPELINE_DIR. Use --overwrite to overwrite.",
                            err=True, fg="red")
                raise click.Abort()
    else:
        # Set PIPELINE_DIR in the .env file
        set_key(env_file, "PIPELINE_DIR", pipeline_dir)
        click.secho(f"Set PIPELINE_DIR in .env file: {pipeline_dir}", fg="blue")

    # Create the pipeline directory if it doesn't exist
    if not os.path.exists(pipeline_dir):
        os.makedirs(pipeline_dir)
        click.secho(f"Created pipeline directory: {pipeline_dir}", fg="blue")
    else:
        click.secho(f"Found existing pipeline directory: {pipeline_dir}", fg="blue")

    # Copy the pipeline template to the pipeline directory
    template_dir = os.path.join(os.path.dirname(__file__), "templates", "pipelines")
    files_to_copy = [f for f in os.listdir(template_dir) if os.path.isfile(os.path.join(template_dir, f))]
    for file in files_to_copy:
        # if file exists, log a warning and skip
        if os.path.exists(os.path.join(pipeline_dir, file)):
            existing_file = os.path.join(pipeline_dir, file)
            click.secho(f"File already exists: {existing_file}", err=True, fg="yellow")
            continue
        else:
            shutil.copy(os.path.join(template_dir, file), pipeline_dir)
            if ctx.obj['debug']:
                click.secho(f"Copied {file} to {pipeline_dir}", fg="blue")

    click.secho(f"Finished initializing Lexy", fg="green")


@cli.command(help="Create docker-compose file")
@click.option('--file',
              default='docker-compose.yaml',
              help='Filepath to save docker-compose file',
              show_default=True,
              type=click.Path(exists=False, file_okay=True, dir_okay=False, writable=True, resolve_path=True))
@click.option('--overwrite', is_flag=True, help='Overwrite existing file')
@click.option('--no-input', is_flag=True, help='Do not prompt for input')
@click.pass_context
def docker(ctx, file, overwrite, no_input):

    if ctx.obj['debug']:
        click.echo(f"Debug mode: {ctx.obj['debug']}")

    # Expand the user's home directory
    default_file = file

    if not no_input:
        # Prompt user
        file = click.prompt("Docker compose file", default=file)
    else:
        # Use default values
        file = default_file

    # File to copy
    template_file = os.path.join(os.path.dirname(__file__), "templates", "docker-compose.yaml")

    # Check if the file already exists
    if os.path.exists(file):
        click.secho(f"File already exists: {file}", err=True, fg="yellow")
        if not no_input:
            click.confirm("Do you want to overwrite the existing file?", abort=True)
            os.remove(file)
            click.secho(f"Removed existing file: {file}", fg="blue")
        else:
            if overwrite:
                os.remove(file)
                click.secho(f"Removed existing file: {file}", fg="blue")
            else:
                click.secho(f"Existing file: {file}. Use --overwrite to overwrite existing file",
                            err=True, fg="red")
                raise click.Abort()

    # Copy the template file to the current working directory
    shutil.copy(template_file, file)
    click.secho(f"Copied docker-compose.yaml to {file}", fg="green")


@cli.group(help="Run tests", invoke_without_command=True)
@click.pass_context
def test(ctx):
    if ctx.invoked_subcommand is None:
        click.echo("Running all tests")


@test.command(help="Run tests for Lexy server")
def server():
    click.echo("Running: pytest -s lexy_tests")


@test.command(help="Run tests for Lexy client")
def client():
    click.echo("Running: pytest -s sdk-python")


if __name__ == "__main__":
    cli(obj={})
