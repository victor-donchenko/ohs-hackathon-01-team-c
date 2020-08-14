# ohs-hackathon-01-team-c
<html>
	<body>
		<style>
		div.a {
			text-align: center;
		}		
		</style>

		<div class="a">
		<h1>Cornovirus Statistics on the Road</h1>
		<h3>Start location in first box and destination in the second</h3>
		<form action="/do_lookup" method="POST">
			<label for="begin_location">Begin Location: </label>
			<input type="text" name="begin_location">
			<h1></h1>
			<label for="end_location">End Location: </label>
			<input type="text" name="end_location">
			<h1></h1>
			<input type="submit">
		</form>
		<p id="output"> </p>
		
		<img src="coronovirus.jfif" alt="coronovirus">
	</div>
	</body>
</html>
