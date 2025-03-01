<script lang="ts">
  import { thebestest } from "./api";
  import { testerinozz } from "@api/besto/api";

  const results = thebestest();
  const results2 = testerinozz({ query: { name: "John" } });
</script>

I AM THE BESTO {$results.loading} - {$results.data?.Hello} - {$results.error}

I AM THE BESTO2 {$results2.loading} - {$results2.data} - {$results2.error}
