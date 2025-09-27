import os
from glob import glob
from setuptools import setup

package_name = 'turtle_shapes'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # install launch files
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='habiba-mowafy',
    maintainer_email='habiba-mowafy@email.com',
    description='Draw shapes in turtlesim',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'shape_node = turtle_shapes.shape_node:main',
            'turtle_commander = turtle_shapes.turtle_commander:main',
        ],
    },
)
