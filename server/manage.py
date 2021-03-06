import logging

from app import create_app, project_manage

app = create_app()


@app.cli.command('deploy', short_help='Deploy project')
def actorcloud_deploy():
    project_manage.project_deploy()


@app.cli.command('upgrade', short_help='Upgrade project')
def actorcloud_upgrade():
    project_manage.project_upgrade()


if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
