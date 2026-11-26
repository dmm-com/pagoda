## Usage

[Helm](https://helm.sh) must be installed to use the charts.  Please refer to
Helm's [documentation](https://helm.sh/docs) to get started.

Once Helm has been set up correctly, add the repo as follows:

  helm repo add airone https://dmm-com.github.io/airone/chart

If you had already added this repo earlier, run `helm repo update` to retrieve
the latest versions of the packages.  You can then run `helm search repo
airone` to see the charts.

To install the airone chart:

    helm install my-airone airone/airone --set airone.secretKey=<random value>

The chart has no default signing key: rendering fails unless `airone.secretKey`
is set or `airone.existingSecret` points at a Secret that contains a `secretKey`
key. Use a unique random value, for example one produced by
`django.core.management.utils.get_random_secret_key()`.

To uninstall the chart:

    helm delete my-airone