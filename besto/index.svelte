<script lang="ts">
  import { thebestest } from "./api";

  const results = thebestest();
</script>

I AM THE BESTO {$results.loading} - {$results.data?.Hello} - {$results.error}
