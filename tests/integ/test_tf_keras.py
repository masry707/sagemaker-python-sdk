# Copyright 2017-2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
from __future__ import absolute_import

import os

import numpy as np
import pytest

from sagemaker.tensorflow import TensorFlow
from tests.integ import DATA_DIR, PYTHON_VERSION, REGION
from tests.integ.timeout import timeout_and_delete_endpoint_by_name, timeout


@pytest.mark.continuous_testing
@pytest.mark.skipif(PYTHON_VERSION != 'py2', reason="TensorFlow image supports only python 2.")
@pytest.mark.skipif(REGION in ['us-west-1', 'eu-west-2', 'ca-central-1'],
                    reason='No ml.p2.xlarge supported in these regions')
def test_keras(sagemaker_session, tf_full_version):
    script_path = os.path.join(DATA_DIR, 'cifar_10', 'source')
    dataset_path = os.path.join(DATA_DIR, 'cifar_10', 'data')

    with timeout(minutes=45):
        estimator = TensorFlow(entry_point='keras_cnn_cifar_10.py',
                               source_dir=script_path,
                               role='SageMakerRole', sagemaker_session=sagemaker_session,
                               hyperparameters={'learning_rate': 1e-4, 'decay': 1e-6},
                               training_steps=50, evaluation_steps=5,
                               train_instance_count=1, train_instance_type='ml.c4.xlarge',
                               train_max_run=45 * 60)

        inputs = estimator.sagemaker_session.upload_data(path=dataset_path, key_prefix='data/cifar10')

        estimator.fit(inputs)

    endpoint_name = estimator.latest_training_job.name
    with timeout_and_delete_endpoint_by_name(endpoint_name, sagemaker_session):
        predictor = estimator.deploy(initial_instance_count=1, instance_type='ml.p2.xlarge')

        data = np.random.randn(32, 32, 3)
        predict_response = predictor.predict(data)
        assert len(predict_response['outputs']['probabilities']['floatVal']) == 10
