<script lang="ts">
  import { testQq } from "./api";

  const results = testQq({ body: { name: "John" } });
</script>

I AM THE BESTO {$results.loading} - {$results.data?.message} - {$results.error}
